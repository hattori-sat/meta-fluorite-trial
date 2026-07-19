from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from mcp.bounded_io import DEFAULT_SKIPPED_DIRS, BoundedRoots
from mcp.config import MCPConfig
from mcp.errors import BoundaryViolation, ConfigurationError, MCPDomainError
from mcp.kernel import AuditHook, EvidenceStore, decode_cursor, encode_cursor, paginate, redact


class PrivacyTests(unittest.TestCase):
    def test_recursive_redaction_removes_credentials_identity_and_network(self) -> None:
        personal_path = "/" + "Users" + "/" + "person" + "/project"
        address = ".".join(("192", "0", "2", "44"))
        ipv6_address = ":".join(
            ("2001", "0db8", "0000", "0000", "0000", "0000", "0000", "0044")
        )
        credential_url = "https://" + "name" + ":" + "pass" + "@" + "example.test"
        account_host = "builder" + "@" + "build-host"
        secret_assignment = "API_" + "TOKEN" + "=fixture-value"
        value = {
            "access_token": "do-not-keep",
            "message": (
                f"Bearer abc.def at {credential_url} from {personal_path} {address} "
                f"via {account_host} and {ipv6_address}; {secret_assignment}"
            ),
        }
        safe = redact(value)
        serialized = json.dumps(safe)
        self.assertNotIn("do-not-keep", serialized)
        self.assertNotIn("abc.def", serialized)
        self.assertNotIn("name:pass", serialized)
        self.assertNotIn(personal_path, serialized)
        self.assertNotIn(address, serialized)
        self.assertNotIn(ipv6_address, serialized)
        self.assertNotIn(account_host, serialized)
        self.assertNotIn("fixture-value", serialized)
        self.assertIn("[REDACTED]", serialized)
        self.assertIn("$HOME", serialized)
        self.assertIn("$IP", serialized)

    def test_redaction_handles_compressed_ipv6_and_private_hostnames(self) -> None:
        compressed = "2001" + ":db8:" + ":44"
        bracketed = "[fd00" + ":" + ":9]"
        private_host = "build-role" + ".internal"
        value = f"observed {compressed} {bracketed} {private_host}; host=other-name"

        safe = str(redact(value))

        self.assertNotIn(compressed, safe)
        self.assertNotIn(bracketed, safe)
        self.assertNotIn(private_host, safe)
        self.assertNotIn("other-name", safe)
        self.assertGreaterEqual(safe.count("$IP"), 2)
        self.assertIn("$HOST", safe)
        self.assertIn("host=[REDACTED_HOST]", safe)

    def test_redaction_removes_unassigned_public_suffix_fqdn(self) -> None:
        fqdn = "node" + ".example" + ".com"
        safe = str(redact(f"connection from {fqdn}"))
        self.assertNotIn(fqdn, safe)
        self.assertIn("$HOST", safe)

    def test_redaction_preserves_dotted_code_identifiers(self) -> None:
        value = "os.path.abspath Path.home config.example.json"
        self.assertEqual(value, redact(value))

    def test_redaction_does_not_treat_slice_notation_as_ipv6(self) -> None:
        self.assertEqual("values[1::2]", redact("values[1::2]"))

    def test_audit_file_receives_only_redacted_arguments(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory, "audit.jsonl")
            warnings = AuditHook(path).emit(
                {"operation": "test", "arguments": {"password": "secret-value"}}
            )
            self.assertEqual([], warnings)
            content = path.read_text(encoding="utf-8")
            self.assertNotIn("secret-value", content)
            self.assertIn("[REDACTED]", content)


class PaginationTests(unittest.TestCase):
    def test_cursor_round_trip_and_page_cap(self) -> None:
        cursor = encode_cursor(2)
        self.assertEqual(2, decode_cursor(cursor))
        page = paginate([0, 1, 2, 3], cursor, 1)
        self.assertEqual([2], page.items)
        self.assertIsNotNone(page.next_cursor)
        self.assertTrue(page.truncated)

    def test_invalid_cursor_and_limit_are_rejected(self) -> None:
        with self.assertRaises(MCPDomainError):
            decode_cursor("not-a-cursor")
        with self.assertRaises(MCPDomainError):
            paginate([1], None, 101)


class EvidenceTests(unittest.TestCase):
    def test_evidence_id_is_stable_and_domain_scoped(self) -> None:
        store = EvidenceStore()
        first = store.record("agl", "observe", {"answer": 1})
        second = store.record("agl", "observe", {"answer": 1})
        third = store.record("yocto", "observe", {"answer": 1})
        self.assertEqual(first, second)
        self.assertNotEqual(first, third)
        self.assertTrue(first.startswith("ev-agl-"))

    def test_envelope_makes_identity_sufficiency_explicit(self) -> None:
        missing = MCPConfig(data={}).kernel("agl").envelope("observe", {"answer": 1})
        self.assertEqual("agl:repository", missing["subject_id"])
        self.assertIsNone(missing["revision_or_image_id"])
        self.assertEqual("insufficient", missing["identity_status"])
        self.assertTrue(any("identity is insufficient" in item for item in missing["unknowns"]))
        self.assertEqual("fluorite.privacy-redaction/v1", missing["redaction_policy"])

        configured = MCPConfig(
            data={
                "domains": {
                    "agl": {
                        "identity": {
                            "subject_id": "agl-fixed-source",
                            "revision_or_image_id": "sha256:0123456789abcdef",
                        }
                    }
                }
            }
        ).kernel("agl").envelope("observe", {"answer": 1})
        self.assertEqual("sufficient", configured["identity_status"])
        self.assertEqual([], configured["unknowns"])
        self.assertNotEqual(missing["evidence_ids"], configured["evidence_ids"])

    def test_response_cap_preserves_resume_locator(self) -> None:
        kernel = MCPConfig(data={"max_response_bytes": 4096}).kernel("yocto")
        envelope = kernel.envelope(
            "read_metadata",
            {
                "metadata_excerpt": {
                    "location": "$METADATA_ROOT/path/to/recipe.bb",
                    "start_line": 1,
                    "next_start_line": 81,
                    "text": "x" * 10000,
                }
            },
        )

        self.assertTrue(envelope["truncated"])
        self.assertEqual(4096, envelope["payload"]["output_cap"])
        self.assertTrue(envelope["payload"]["resume_locators"])
        locator = envelope["payload"]["resume_locators"][0]
        self.assertEqual("$METADATA_ROOT/path/to/recipe.bb", locator["location"])
        self.assertEqual(81, locator["next_start_line"])

    def test_identity_configuration_rejects_unbounded_values(self) -> None:
        config = MCPConfig(
            data={
                "domains": {
                    "agl": {
                        "identity": {
                            "subject_id": "invalid/value",
                            "revision_or_image_id": "fixed",
                        }
                    }
                }
            }
        )
        with self.assertRaises(ConfigurationError):
            config.kernel("agl")

    def test_repository_root_alias_cannot_be_overridden(self) -> None:
        config = MCPConfig(
            data={
                "domains": {
                    "yocto": {
                        "roots": {"repository": "/role/unverified/repository"}
                    }
                }
            }
        )
        with self.assertRaises(ConfigurationError):
            config.roots("yocto")


class FilesystemBoundaryTests(unittest.TestCase):
    def test_relative_read_and_literal_search_are_bounded(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            Path(root, "recipe.bb").write_text('SUMMARY = "Fluorite"\n', encoding="utf-8")
            sources = BoundedRoots({"metadata": root}, extensions={".bb"})
            excerpt = sources.read_lines("metadata", "recipe.bb", line_count=5)
            self.assertIn("Fluorite", excerpt["text"])
            page, scan_cap = sources.search_literal("metadata", "fluorite")
            self.assertFalse(scan_cap)
            self.assertEqual(1, len(page.items))
            self.assertEqual("$METADATA_ROOT/recipe.bb", page.items[0]["location"])

    def test_traversal_and_outside_symlink_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as outside:
            root = Path(directory)
            outside_file = Path(outside, "outside.bb")
            outside_file.write_text("SECRET = 1\n", encoding="utf-8")
            Path(root, "link.bb").symlink_to(outside_file)
            sources = BoundedRoots({"metadata": root}, extensions={".bb"})
            with self.assertRaises(BoundaryViolation):
                sources.resolve("metadata", "../outside.bb")
            with self.assertRaises(BoundaryViolation):
                sources.resolve("metadata", "link.bb")

    def test_sensitive_role_config_is_neither_walked_nor_directly_read(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            role_config = root / ".fluorite-mcp" / "config.json"
            role_config.parent.mkdir()
            role_config.write_text('{"audit_file": "/role/private/path"}\n', encoding="utf-8")
            sources = BoundedRoots({"repository": root}, extensions={".json"})

            page, incomplete = sources.list_files("repository")

            self.assertEqual([], page.items)
            self.assertFalse(incomplete)
            with self.assertRaises(BoundaryViolation):
                sources.read_lines("repository", ".fluorite-mcp/config.json")
            (root / "visible").symlink_to(role_config.parent, target_is_directory=True)
            with self.assertRaises(BoundaryViolation):
                sources.read_lines("repository", "visible/config.json")
            with self.assertRaises(BoundaryViolation):
                BoundedRoots({"sensitive": role_config.parent}, extensions={".json"})

    def test_catalog_includes_large_binary_but_text_scan_reports_omission(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            large = b"x" * (2 * 1024 * 1024 + 1)
            Path(root, "scene.glb").write_bytes(large)
            Path(root, "oversized.txt").write_bytes(large)

            catalog = BoundedRoots({"assets": root}, extensions={".glb"})
            page, truncated = catalog.list_files("assets")
            self.assertFalse(truncated)
            self.assertEqual("scene.glb", page.items[0]["relative_path"])
            with self.assertRaises(MCPDomainError):
                catalog.read_lines("assets", "scene.glb")

            text = BoundedRoots({"source": root}, extensions={".txt"})
            matches, scan_truncated = text.search_literal("source", "needle")
            self.assertEqual([], matches.items)
            self.assertTrue(scan_truncated)

    def test_allowlisted_bitbake_task_log_name_has_bounded_access(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            task_log = Path(root, "temp", "log.do_compile.1234")
            task_log.parent.mkdir()
            task_log.write_text("line one\nline two\n", encoding="utf-8")
            sources = BoundedRoots(
                {"build": root},
                extensions={".log"},
                allowed_name_patterns=(r"log\.do_[A-Za-z0-9_+.-]+(?:\.[0-9]+)?",),
            )
            excerpt = sources.tail_lines("build", "temp/log.do_compile.1234")
            self.assertIn("line two", excerpt["text"])

    def test_oversized_task_log_uses_bounded_streaming_tail(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            task_log = root / "log.do_compile.1234"
            task_log.write_bytes(b"old evidence\n" * 180000 + b"final marker\n")
            sources = BoundedRoots(
                {"build": root},
                extensions={".log"},
                allowed_name_patterns=(r"log\.do_[A-Za-z0-9_+.-]+(?:\.[0-9]+)?",),
            )

            excerpt = sources.tail_lines("build", task_log.name, line_count=5)

            self.assertIn("final marker", excerpt["text"])
            self.assertTrue(excerpt["truncated"])
            self.assertIsNone(excerpt["total_lines"])
            self.assertLessEqual(excerpt["scanned_tail_bytes"], 256 * 1024)

    def test_yocto_policy_discovers_task_logs_below_build_tmp(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            task_log = Path(root, "tmp", "work", "machine", "recipe", "temp", "log.do_compile.1234")
            task_log.parent.mkdir(parents=True)
            task_log.write_text("compile evidence\n", encoding="utf-8")
            sources = BoundedRoots(
                {"build": root},
                extensions={".log"},
                allowed_name_patterns=(r"log\.do_[A-Za-z0-9_+.-]+(?:\.[0-9]+)?",),
                skipped_dirs=DEFAULT_SKIPPED_DIRS - {"tmp"},
            )

            page, truncated = sources.list_files("build", name_terms=("log.do_",))

            self.assertFalse(truncated)
            self.assertEqual(1, len(page.items))
            self.assertEqual(
                "tmp/work/machine/recipe/temp/log.do_compile.1234",
                page.items[0]["relative_path"],
            )

    def test_catalog_cap_is_applied_after_name_filter(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for number in range(3):
                (root / f"recipe-{number}.bb").write_text(
                    "SUMMARY = 'fixture'\n", encoding="utf-8"
                )
            task_log = root / "log.do_compile.1234"
            task_log.write_text("compile evidence\n", encoding="utf-8")
            sources = BoundedRoots(
                {"build": root},
                extensions={".bb", ".log"},
                allowed_name_patterns=(r"log\.do_[A-Za-z0-9_+.-]+(?:\.[0-9]+)?",),
                max_scan_files=1,
            )

            page, incomplete = sources.list_files("build", name_terms=("log.do_",))

            self.assertEqual(
                ["log.do_compile.1234"],
                [item["relative_path"] for item in page.items],
            )
            self.assertFalse(incomplete)

    def test_search_marks_unreadable_file_as_incomplete(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            blocked = root / "blocked.bb"
            blocked.write_text("needle\n", encoding="utf-8")
            sources = BoundedRoots({"metadata": root}, extensions={".bb"})
            original_open = Path.open

            def controlled_open(path: Path, *args: object, **kwargs: object):
                if path.resolve() == blocked.resolve():
                    raise OSError("fixture read failure")
                return original_open(path, *args, **kwargs)

            with patch.object(Path, "open", controlled_open):
                page, incomplete = sources.search_literal("metadata", "needle")

            self.assertEqual([], page.items)
            self.assertTrue(incomplete)

    def test_walk_marks_unreadable_subtree_as_incomplete(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sources = BoundedRoots({"metadata": root}, extensions={".bb"})

            def failing_walk(*_args: object, **kwargs: object):
                onerror = kwargs["onerror"]
                onerror(OSError("fixture directory failure"))
                return iter(())

            with patch("mcp.bounded_io.os.walk", failing_walk):
                page, incomplete = sources.list_files("metadata")

            self.assertEqual([], page.items)
            self.assertTrue(incomplete)


if __name__ == "__main__":
    unittest.main()
