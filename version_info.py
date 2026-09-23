"""Canonical embedded identity for the Hermes MCP Bridge.

Release preparation stamps RELEASE_IDENTIFIER and EMBEDDED_SOURCE_REVISION before
the signed tag.  An embedded revision identifies the reviewed build input, not the
self-referential final tag commit; the signed tag remains authoritative for that
commit. Runtime never requires Git; Git metadata is optional enrichment for an
unpacked working tree only.
"""

BRIDGE_VERSION = "1.2.2"
RELEASE_IDENTIFIER = "v1.2.2"
EMBEDDED_SOURCE_REVISION = "079f1fc2386de62cfa52a5bbe38645e4efdbdd2e"
BUILD_PROVENANCE = "release"
MCP_DISCOVERY_COUNT = 27
CONFIG_SCHEMA_VERSION = 1
