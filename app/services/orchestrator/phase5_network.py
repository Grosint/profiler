"""
Phase 5: Network & Interaction Intelligence

Graph construction, centrality metrics, community detection using NetworkX.
"""

import logging
from typing import Any, Dict, List

from app.models.scraped_data import ScrapedData

logger = logging.getLogger(__name__)


class Phase5Network:
    """Handles network and interaction intelligence analysis."""

    async def execute(
        self, scraped_items: List[ScrapedData], features: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Graph construction, centrality metrics, community detection using NetworkX."""
        try:
            import networkx as nx
        except ImportError:
            logger.warning("NetworkX not available, using fallback")
            return self._fallback(scraped_items)

        # Build interaction graph
        G = nx.Graph()
        node_attributes = {}

        # Extract subject identifier (from profile or first item)
        subject_id = None
        if scraped_items:
            # Try to get subject from metadata
            for item in scraped_items:
                if item.metadata and "username" in item.metadata:
                    subject_id = str(item.metadata["username"]).lower()
                    break
                if item.metadata and "author" in item.metadata:
                    subject_id = str(item.metadata["author"]).lower()
                    break

        if not subject_id:
            subject_id = "subject"

        # Add subject node
        G.add_node(subject_id)
        node_attributes[subject_id] = {"type": "subject", "platforms": set()}

        # Extract interactions and build edges
        for item in scraped_items:
            platform = item.platform.value if item.platform else "unknown"
            if subject_id in node_attributes:
                node_attributes[subject_id]["platforms"].add(platform)

            if item.metadata:
                # Extract mentions
                if "mentions" in item.metadata:
                    mentions = item.metadata.get("mentions", [])
                    if isinstance(mentions, list):
                        for mention in mentions:
                            mention_id = str(mention).lower()
                            if mention_id != subject_id:
                                G.add_node(mention_id)
                                G.add_edge(subject_id, mention_id, weight=1, type="mention")
                                if mention_id not in node_attributes:
                                    node_attributes[mention_id] = {"type": "user", "platforms": set()}
                                node_attributes[mention_id]["platforms"].add(platform)

                # Extract replies
                if "replies_to" in item.metadata:
                    replies_to = item.metadata.get("replies_to")
                    if replies_to:
                        reply_id = str(replies_to).lower()
                        if reply_id != subject_id:
                            G.add_node(reply_id)
                            if G.has_edge(subject_id, reply_id):
                                G[subject_id][reply_id]["weight"] += 1
                            else:
                                G.add_edge(subject_id, reply_id, weight=1, type="reply")
                            if reply_id not in node_attributes:
                                node_attributes[reply_id] = {"type": "user", "platforms": set()}
                            node_attributes[reply_id]["platforms"].add(platform)

                # Extract retweets/shares
                if "retweeted_by" in item.metadata:
                    retweeters = item.metadata.get("retweeted_by", [])
                    if isinstance(retweeters, list):
                        for retweeter in retweeters:
                            retweeter_id = str(retweeter).lower()
                            if retweeter_id != subject_id:
                                G.add_node(retweeter_id)
                                if G.has_edge(subject_id, retweeter_id):
                                    G[subject_id][retweeter_id]["weight"] += 1
                                else:
                                    G.add_edge(subject_id, retweeter_id, weight=1, type="share")
                                if retweeter_id not in node_attributes:
                                    node_attributes[retweeter_id] = {"type": "user", "platforms": set()}
                                node_attributes[retweeter_id]["platforms"].add(platform)

        # Calculate centrality metrics
        influence_score = 0.0
        degree_score = 0.0
        betweenness_score = 0.0

        if G.has_node(subject_id) and G.degree(subject_id) > 0:
            try:
                # Degree centrality
                degree_centrality = nx.degree_centrality(G)
                degree_score = degree_centrality.get(subject_id, 0.0)

                # Betweenness centrality (if graph is connected)
                if nx.is_connected(G) or len(list(nx.connected_components(G))) == 1:
                    betweenness = nx.betweenness_centrality(G)
                    betweenness_score = betweenness.get(subject_id, 0.0)
                else:
                    # Calculate for largest connected component
                    largest_cc = max(nx.connected_components(G), key=len)
                    if subject_id in largest_cc:
                        subgraph = G.subgraph(largest_cc)
                        betweenness = nx.betweenness_centrality(subgraph)
                        betweenness_score = betweenness.get(subject_id, 0.0)
                    else:
                        betweenness_score = 0.0

                # Eigenvector centrality
                try:
                    eigenvector = nx.eigenvector_centrality(G, max_iter=100)
                    eigenvector_score = eigenvector.get(subject_id, 0.0)
                except:
                    eigenvector_score = 0.0

                # Combined influence score (weighted average)
                influence_score = (degree_score * 0.5) + (betweenness_score * 0.3) + (eigenvector_score * 0.2)
            except Exception as e:
                logger.warning(f"Centrality calculation failed: {e}")
                # Fallback to simple degree
                degree_score = min(1.0, G.degree(subject_id) / 100.0)
                influence_score = degree_score

        # Community detection using Louvain algorithm
        community_count = 1
        try:
            import community as community_louvain

            communities = community_louvain.best_partition(G)
            community_count = len(set(communities.values()))
        except ImportError:
            # Fallback to NetworkX community detection
            try:
                communities = list(nx.community.greedy_modularity_communities(G))
                community_count = len(communities)
            except:
                # Last resort: use connected components
                community_count = len(list(nx.connected_components(G)))

        unique_connections = G.number_of_nodes() - 1  # Exclude subject

        return {
            "influenceScore": round(influence_score, 3),
            "communityCount": community_count,
            "uniqueConnections": unique_connections,
            "degreeCentrality": round(degree_score, 3),
            "betweennessCentrality": round(betweenness_score, 3),
        }

    def _fallback(self, scraped_items: List[ScrapedData]) -> Dict[str, Any]:
        """Fallback network analysis without NetworkX."""
        mentioned_users = set()
        for item in scraped_items:
            if item.metadata:
                if "mentions" in item.metadata:
                    mentions = item.metadata.get("mentions", [])
                    if isinstance(mentions, list):
                        mentioned_users.update(mentions)
                if "replies_to" in item.metadata:
                    replies_to = item.metadata.get("replies_to")
                    if replies_to:
                        mentioned_users.add(str(replies_to))

        unique_connections = len(mentioned_users)
        total_posts = len([item for item in scraped_items if item.rawContent])
        connection_density = unique_connections / max(total_posts, 1) if total_posts > 0 else 0
        influence_score = min(1.0, connection_density / 10.0)

        platforms = set(item.platform.value for item in scraped_items)
        community_count = len(platforms)

        return {
            "influenceScore": round(influence_score, 3),
            "communityCount": community_count,
            "uniqueConnections": unique_connections,
        }
