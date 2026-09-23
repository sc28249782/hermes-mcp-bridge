"""Canonical embedded identity for the Hermes MCP Bridge.

Release preparation stamps RELEASE_IDENTIFIER and EMBEDDED_SOURCE_REVISION before
the signed tag.  Runtime never requires Git; Git metadata is optional enrichment
for an unpacked working tree only.
"""

BRIDGE_VERSION = "1.2.2"
RELEASE_IDENTIFIER = "v1.2.2-candidate"
EMBEDDED_SOURCE_REVISION = "unknown"
BUILD_PROVENANCE = "development"
MCP_DISCOVERY_COUNT = 27
CONFIG_SCHEMA_VERSION = 1
