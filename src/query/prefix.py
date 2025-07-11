from typing import List, Optional
from llama_index.core.postprocessor.types import BaseNodePostprocessor
from llama_index.core.schema import NodeWithScore, MetadataMode

class MetadataPrefixPostProcessor(BaseNodePostprocessor):
    """Prepend a metadata field to the node text instead of replacing it."""
    meta_key: str
    sep: str = " – "

    @classmethod
    def class_name(cls) -> str:
        return "MetadataPrefixPostProcessor"

    def _postprocess_nodes(
        self,
        nodes: List[NodeWithScore],
        query_str: Optional[str] = None,
    ) -> List[NodeWithScore]:
        for n in nodes:
            meta = n.node.metadata.get(self.meta_key)
            if meta:
                original = n.node.get_content(metadata_mode=MetadataMode.NONE)
                n.node.set_content(f"{meta}{self.sep}{original}")
        return nodes
