"""Canonical embedded identity for the Hermes MCP Bridge.

Release preparation stamps RELEASE_IDENTIFIER and EMBEDDED_SOURCE_REVISION before
the signed tag.  An embedded revision identifies the reviewed build input, not the
self-referential final tag commit; the signed tag remains authoritative for that
commit. Runtime never requires Git; Git metadata is optional enrichment for an
unpacked working tree only.
"""

BRIDGE_VERSION = "1.2.8"
RELEASE_IDENTIFIER = "v1.2.8"
EMBEDDED_SOURCE_REVISION = "887436f359683f0215f1993d7cb0c9035ec93571"
BUILD_PROVENANCE = "release"
MCP_DISCOVERY_COUNT = 27
CONFIG_SCHEMA_VERSION = 1
