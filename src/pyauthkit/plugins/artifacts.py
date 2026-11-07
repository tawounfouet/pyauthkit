"""Pre-install wheel identity check using an independently trusted digest.

This is a limited deployment-stage artifact check, NOT an attestation that
EntryPoint.load() will later execute these bytes. The host must obtain the
expected SHA-256 from a trusted channel independent of the wheel itself.
No zip extraction, plugin import, signature verification or installation.
"""

import hashlib
import hmac
import re
from configparser import ConfigParser
from email.parser import BytesParser
from email.policy import default
from pathlib import Path
from zipfile import ZipFile

from .admission import PluginGrant
from .discovery import PluginAdmissionRejected, canonical_distribution

_HEX_DIGEST = re.compile(r"[0-9a-f]{64}\Z")
_MAX_WHEEL_SIZE = 50 * 1024 * 1024
_MAX_META_SIZE = 64 * 1024
_MAX_MEMBERS = 10000


class _CaseSensitiveEntryPoints(ConfigParser):
    """Keep entry-point names case-sensitive when checking an exact grant."""

    def optionxform(self, optionstr: str) -> str:
        return optionstr


def verify_preinstall_wheel_digest(
    wheel_path: Path, *, expected_sha256: str, grant: PluginGrant
) -> None:
    """Reject an unexpected wheel before installation, without executing it.

    Does NOT authorize a plugin factory, pin an imported module, prevent
    mutable filesystem races, or establish an independent trust anchor.
    """
    try:
        if (
            not isinstance(wheel_path, Path)
            or wheel_path.suffix != ".whl"
            or wheel_path.is_symlink()
            or not isinstance(expected_sha256, str)
            or _HEX_DIGEST.fullmatch(expected_sha256) is None
            or not isinstance(grant, PluginGrant)
        ):
            raise PluginAdmissionRejected("invalid host wheel verification request")
        if not wheel_path.is_file() or wheel_path.stat().st_size > _MAX_WHEEL_SIZE:
            raise PluginAdmissionRejected("wheel artifact unavailable or oversized")

        digest = hashlib.sha256()
        count = 0
        with wheel_path.open("rb") as source:
            while data := source.read(1024 * 1024):
                count += len(data)
                if count > _MAX_WHEEL_SIZE:
                    raise PluginAdmissionRejected("wheel artifact unavailable or oversized")
                digest.update(data)
        if not hmac.compare_digest(digest.hexdigest(), expected_sha256):
            raise PluginAdmissionRejected("wheel digest not approved")

        with ZipFile(wheel_path, "r") as archive:
            members = archive.infolist()
            names = [member.filename for member in members]
            if (
                len(members) > _MAX_MEMBERS
                or len(names) != len(set(names))
                or any(
                    name.startswith("/") or ".." in name.split("/") or "\\" in name
                    for name in names
                )
            ):
                raise PluginAdmissionRejected("invalid wheel archive")
            metadata = [
                m
                for m in members
                if m.filename.count("/") == 1 and m.filename.endswith(".dist-info/METADATA")
            ]
            if len(metadata) != 1 or metadata[0].file_size > _MAX_META_SIZE:
                raise PluginAdmissionRejected("missing or ambiguous wheel metadata")
            info = archive.read(metadata[0])
            message = BytesParser(policy=default).parsebytes(info, headersonly=True)
            names_header = message.get_all("Name", [])
            versions_header = message.get_all("Version", [])
            if len(names_header) != 1 or len(versions_header) != 1:
                raise PluginAdmissionRejected("invalid wheel identity")
            wheel_name = names_header[0]
            wheel_version = versions_header[0]
            if (
                not isinstance(wheel_name, str)
                or not isinstance(wheel_version, str)
                or canonical_distribution(wheel_name) != grant.distribution
                or wheel_version != grant.version
            ):
                raise PluginAdmissionRejected("wheel identity not approved")

            prefix = metadata[0].filename.removesuffix("METADATA")
            entry_info = [m for m in members if m.filename == prefix + "entry_points.txt"]
            if len(entry_info) != 1 or entry_info[0].file_size > _MAX_META_SIZE:
                raise PluginAdmissionRejected("wheel entry points missing or ambiguous")
            raw_entries = archive.read(entry_info[0]).decode("utf-8")
            parser = _CaseSensitiveEntryPoints(interpolation=None, strict=True)
            parser.read_string(raw_entries)
            if (
                not parser.has_section(grant.group)
                or not parser.has_option(grant.group, grant.name)
                or parser.get(grant.group, grant.name) != grant.target
            ):
                raise PluginAdmissionRejected("wheel entry point not approved")
    except PluginAdmissionRejected:
        raise
    except Exception:
        raise PluginAdmissionRejected("wheel artifact inspection failed") from None
