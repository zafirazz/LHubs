"""
Graph Pattern Detector - Detects money laundering patterns using graph analysis.
Implements detection for: Fan-out, Fan-in, Gather-scatter, Scatter-gather, 
Simple cycle, Random graph structures, Bipartite, Stack/layered graph.
"""

import logging
from typing import Dict, List, Any, Set, Tuple, Optional
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@dataclass
class PatternMatch:
    """Represents a detected laundering pattern."""
    pattern_type: str
    severity: str  # "high", "medium", "low"
    description: str
    accounts_involved: List[str]
    transactions_involved: List[str]
    total_amount: float
    time_window_days: int
    confidence: float  # 0.0 to 1.0
    metadata: Dict[str, Any]


class TransactionGraph:
    """Graph representation of transactions for pattern detection."""
    
    def __init__(self):
        self.nodes: Set[str] = set()  # Account IDs
        self.edges: Dict[Tuple[str, str], List[Dict[str, Any]]] = defaultdict(list)  # (from, to) -> transactions
        self.in_degree: Dict[str, int] = defaultdict(int)  # Incoming transaction count
        self.out_degree: Dict[str, int] = defaultdict(int)  # Outgoing transaction count
        self.node_metadata: Dict[str, Dict[str, Any]] = defaultdict(dict)
    
    def add_transaction(self, tx: Dict[str, Any]):
        """Add a transaction to the graph."""
        from_account = str(tx.get("from_account", ""))
        to_account = str(tx.get("to_account", ""))
        
        if not from_account or not to_account or from_account == to_account:
            return  # Skip invalid transactions
        
        self.nodes.add(from_account)
        self.nodes.add(to_account)
        
        edge = (from_account, to_account)
        self.edges[edge].append(tx)
        
        self.out_degree[from_account] += 1
        self.in_degree[to_account] += 1
        
        # Store metadata
        if from_account not in self.node_metadata:
            self.node_metadata[from_account] = {
                "total_sent": 0.0,
                "total_received": 0.0,
                "transaction_count": 0
            }
        if to_account not in self.node_metadata:
            self.node_metadata[to_account] = {
                "total_sent": 0.0,
                "total_received": 0.0,
                "transaction_count": 0
            }
        
        amount = float(tx.get("amount", 0))
        self.node_metadata[from_account]["total_sent"] += amount
        self.node_metadata[to_account]["total_received"] += amount
        self.node_metadata[from_account]["transaction_count"] += 1
        self.node_metadata[to_account]["transaction_count"] += 1
    
    def get_neighbors(self, account: str, direction: str = "out") -> List[str]:
        """Get neighbors of an account (outgoing or incoming)."""
        neighbors = []
        if direction == "out":
            for (from_acc, to_acc), txs in self.edges.items():
                if from_acc == account:
                    neighbors.append(to_acc)
        else:  # direction == "in"
            for (from_acc, to_acc), txs in self.edges.items():
                if to_acc == account:
                    neighbors.append(from_acc)
        return list(set(neighbors))


class GraphPatternDetector:
    """
    Detects money laundering patterns in transaction graphs.
    
    Patterns detected:
    1. Fan-out: One account sends to many accounts
    2. Fan-in: Many accounts send to one account
    3. Gather-scatter: Money gathered then scattered
    4. Scatter-gather: Money scattered then gathered
    5. Simple cycle: Circular transactions
    6. Random graph: Complex interconnected structure
    7. Bipartite: Two distinct groups with transactions only between groups
    8. Stack/layered: Multi-layer transaction structure
    """
    
    def __init__(self, 
                 fan_threshold: int = 5,
                 cycle_min_length: int = 3,
                 cycle_max_length: int = 10,
                 amount_threshold: float = 10000.0):
        self.fan_threshold = fan_threshold  # Min connections for fan pattern
        self.cycle_min_length = cycle_min_length
        self.cycle_max_length = cycle_max_length
        self.amount_threshold = amount_threshold
    
    def detect_all_patterns(self, transactions: List[Dict[str, Any]]) -> List[PatternMatch]:
        """Detect all laundering patterns in transaction data."""
        # Build graph
        graph = TransactionGraph()
        for tx in transactions:
            graph.add_transaction(tx)
        
        if len(graph.nodes) < 2:
            return []  # Need at least 2 accounts
        
        patterns = []
        
        # Detect each pattern type
        patterns.extend(self._detect_fan_out(graph))
        patterns.extend(self._detect_fan_in(graph))
        patterns.extend(self._detect_gather_scatter(graph))
        patterns.extend(self._detect_scatter_gather(graph))
        patterns.extend(self._detect_simple_cycles(graph))
        patterns.extend(self._detect_bipartite(graph))
        patterns.extend(self._detect_layered_structure(graph))
        patterns.extend(self._detect_random_graph(graph))
        
        # Sort by severity and confidence
        patterns.sort(key=lambda p: (
            {"high": 0, "medium": 1, "low": 2}[p.severity],
            -p.confidence
        ))
        
        return patterns
    
    def _detect_fan_out(self, graph: TransactionGraph) -> List[PatternMatch]:
        """Detect Fan-out pattern: One account sends to many."""
        patterns = []
        
        for account in graph.nodes:
            out_degree = graph.out_degree[account]
            if out_degree >= self.fan_threshold:
                # Get all outgoing transactions
                outgoing_txs = []
                total_amount = 0.0
                recipients = set()
                
                for (from_acc, to_acc), txs in graph.edges.items():
                    if from_acc == account:
                        recipients.add(to_acc)
                        for tx in txs:
                            outgoing_txs.append(tx.get("transaction_id", ""))
                            total_amount += float(tx.get("amount", 0))
                
                if len(recipients) >= self.fan_threshold:
                    severity = "high" if out_degree >= 10 else "medium" if out_degree >= 7 else "low"
                    confidence = min(1.0, out_degree / 20.0)  # Higher degree = higher confidence
                    
                    patterns.append(PatternMatch(
                        pattern_type="fan_out",
                        severity=severity,
                        description=f"Fan-out pattern: Account {account} sends to {len(recipients)} different accounts",
                        accounts_involved=[account] + list(recipients),
                        transactions_involved=outgoing_txs[:50],  # Limit to first 50
                        total_amount=total_amount,
                        time_window_days=30,  # Approximate
                        confidence=confidence,
                        metadata={
                            "source_account": account,
                            "recipient_count": len(recipients),
                            "out_degree": out_degree
                        }
                    ))
        
        return patterns
    
    def _detect_fan_in(self, graph: TransactionGraph) -> List[PatternMatch]:
        """Detect Fan-in pattern: Many accounts send to one."""
        patterns = []
        
        for account in graph.nodes:
            in_degree = graph.in_degree[account]
            if in_degree >= self.fan_threshold:
                # Get all incoming transactions
                incoming_txs = []
                total_amount = 0.0
                senders = set()
                
                for (from_acc, to_acc), txs in graph.edges.items():
                    if to_acc == account:
                        senders.add(from_acc)
                        for tx in txs:
                            incoming_txs.append(tx.get("transaction_id", ""))
                            total_amount += float(tx.get("amount", 0))
                
                if len(senders) >= self.fan_threshold:
                    severity = "high" if in_degree >= 10 else "medium" if in_degree >= 7 else "low"
                    confidence = min(1.0, in_degree / 20.0)
                    
                    patterns.append(PatternMatch(
                        pattern_type="fan_in",
                        severity=severity,
                        description=f"Fan-in pattern: {len(senders)} accounts send to account {account}",
                        accounts_involved=[account] + list(senders),
                        transactions_involved=incoming_txs[:50],
                        total_amount=total_amount,
                        time_window_days=30,
                        confidence=confidence,
                        metadata={
                            "destination_account": account,
                            "sender_count": len(senders),
                            "in_degree": in_degree
                        }
                    ))
        
        return patterns
    
    def _detect_gather_scatter(self, graph: TransactionGraph) -> List[PatternMatch]:
        """Detect Gather-scatter: Money gathered then scattered."""
        patterns = []
        
        # Find accounts that receive from many (gather) AND send to many (scatter)
        for account in graph.nodes:
            in_degree = graph.in_degree[account]
            out_degree = graph.out_degree[account]
            
            if in_degree >= self.fan_threshold and out_degree >= self.fan_threshold:
                # This account gathers and scatters
                senders = set()
                recipients = set()
                all_txs = []
                total_amount = 0.0
                
                for (from_acc, to_acc), txs in graph.edges.items():
                    if to_acc == account:  # Incoming
                        senders.add(from_acc)
                    elif from_acc == account:  # Outgoing
                        recipients.add(to_acc)
                    
                    if from_acc == account or to_acc == account:
                        for tx in txs:
                            all_txs.append(tx.get("transaction_id", ""))
                            total_amount += float(tx.get("amount", 0))
                
                if len(senders) >= self.fan_threshold and len(recipients) >= self.fan_threshold:
                    severity = "high" if (in_degree + out_degree) >= 15 else "medium"
                    confidence = min(1.0, (in_degree + out_degree) / 30.0)
                    
                    patterns.append(PatternMatch(
                        pattern_type="gather_scatter",
                        severity=severity,
                        description=f"Gather-scatter pattern: Account {account} receives from {len(senders)} accounts and sends to {len(recipients)} accounts",
                        accounts_involved=[account] + list(senders) + list(recipients),
                        transactions_involved=all_txs[:50],
                        total_amount=total_amount,
                        time_window_days=30,
                        confidence=confidence,
                        metadata={
                            "hub_account": account,
                            "sender_count": len(senders),
                            "recipient_count": len(recipients),
                            "in_degree": in_degree,
                            "out_degree": out_degree
                        }
                    ))
        
        return patterns
    
    def _detect_scatter_gather(self, graph: TransactionGraph) -> List[PatternMatch]:
        """Detect Scatter-gather: Money scattered then gathered (opposite flow)."""
        # Similar to gather-scatter but we look for the pattern in reverse
        # Find accounts that send to many, then trace if those recipients send to a common destination
        patterns = []
        
        # Find accounts with high out-degree (scatterers)
        scatterers = [acc for acc in graph.nodes if graph.out_degree[acc] >= self.fan_threshold]
        
        for scatterer in scatterers:
            # Get all recipients
            recipients = graph.get_neighbors(scatterer, "out")
            
            # Check if multiple recipients send to a common account (gatherer)
            recipient_targets = defaultdict(set)
            for recipient in recipients:
                targets = graph.get_neighbors(recipient, "out")
                for target in targets:
                    recipient_targets[target].add(recipient)
            
            # Find targets that receive from multiple scatterer recipients
            for target, sources in recipient_targets.items():
                if len(sources) >= self.fan_threshold:
                    # Found scatter-gather pattern
                    all_accounts = [scatterer, target] + list(sources)
                    all_txs = []
                    total_amount = 0.0
                    
                    # Collect transactions
                    for (from_acc, to_acc), txs in graph.edges.items():
                        if (from_acc == scatterer and to_acc in sources) or \
                           (from_acc in sources and to_acc == target):
                            for tx in txs:
                                all_txs.append(tx.get("transaction_id", ""))
                                total_amount += float(tx.get("amount", 0))
                    
                    severity = "high" if len(sources) >= 7 else "medium"
                    confidence = min(1.0, len(sources) / 15.0)
                    
                    patterns.append(PatternMatch(
                        pattern_type="scatter_gather",
                        severity=severity,
                        description=f"Scatter-gather pattern: Account {scatterer} sends to {len(recipients)} accounts, {len(sources)} of which send to {target}",
                        accounts_involved=all_accounts,
                        transactions_involved=all_txs[:50],
                        total_amount=total_amount,
                        time_window_days=30,
                        confidence=confidence,
                        metadata={
                            "scatterer_account": scatterer,
                            "gatherer_account": target,
                            "intermediate_count": len(sources)
                        }
                    ))
        
        return patterns
    
    def _detect_simple_cycles(self, graph: TransactionGraph) -> List[PatternMatch]:
        """Detect simple cycles (circular transactions)."""
        patterns = []
        visited_cycles = set()
        
        # Limit cycle detection to high-degree nodes for performance
        high_degree_nodes = [acc for acc in graph.nodes 
                            if graph.in_degree[acc] + graph.out_degree[acc] >= 3]
        
        if len(high_degree_nodes) > 100:
            # Too many nodes, sample them
            import random
            high_degree_nodes = random.sample(high_degree_nodes, 100)
        
        def find_cycles(start: str, current: str, path: List[str], visited: Set[str], max_depth: int, max_cycles: int = 10):
            """DFS to find cycles (limited)."""
            if len(path) > max_depth or len(visited_cycles) >= max_cycles:
                return []
            
            cycles = []
            neighbors = graph.get_neighbors(current, "out")
            
            # Limit neighbors to check
            neighbors = neighbors[:20]  # Limit to first 20 neighbors
            
            for neighbor in neighbors:
                if neighbor == start and len(path) >= self.cycle_min_length:
                    # Found a cycle
                    cycle_tuple = tuple(sorted(path + [start]))
                    if cycle_tuple not in visited_cycles:
                        visited_cycles.add(cycle_tuple)
                        cycles.append(path + [start])
                        if len(visited_cycles) >= max_cycles:
                            break
                elif neighbor not in visited and len(path) < max_depth:
                    cycles.extend(find_cycles(start, neighbor, path + [neighbor], visited | {neighbor}, max_depth, max_cycles))
                    if len(visited_cycles) >= max_cycles:
                        break
            
            return cycles
        
        # Find cycles starting from high-degree nodes only
        for account in high_degree_nodes:
            cycles = find_cycles(account, account, [account], {account}, min(self.cycle_max_length, 6))  # Limit max depth
            
            for cycle in cycles:
                if len(cycle) >= self.cycle_min_length:
                    # Collect transactions in cycle
                    cycle_txs = []
                    total_amount = 0.0
                    
                    for i in range(len(cycle) - 1):
                        from_acc = cycle[i]
                        to_acc = cycle[i + 1]
                        edge = (from_acc, to_acc)
                        if edge in graph.edges:
                            for tx in graph.edges[edge]:
                                cycle_txs.append(tx.get("transaction_id", ""))
                                total_amount += float(tx.get("amount", 0))
                    
                    severity = "high" if len(cycle) <= 4 else "medium"  # Shorter cycles are more suspicious
                    confidence = 0.8 if len(cycle) <= 5 else 0.6
                    
                    patterns.append(PatternMatch(
                        pattern_type="simple_cycle",
                        severity=severity,
                        description=f"Simple cycle pattern: Circular transaction path involving {len(cycle)} accounts: {' -> '.join(cycle[:5])}...",
                        accounts_involved=cycle,
                        transactions_involved=cycle_txs[:50],
                        total_amount=total_amount,
                        time_window_days=30,
                        confidence=confidence,
                        metadata={
                            "cycle_length": len(cycle),
                            "cycle_path": cycle
                        }
                    ))
        
        return patterns
    
    def _detect_bipartite(self, graph: TransactionGraph) -> List[PatternMatch]:
        """Detect bipartite structure: Two distinct groups with transactions only between groups."""
        patterns = []
        
        # Try to partition graph into two sets
        # Simple heuristic: Find two groups with many cross-connections
        
        if len(graph.nodes) < 4:
            return patterns  # Need at least 4 nodes
        
        # Find accounts with high connectivity
        high_degree_nodes = [acc for acc in graph.nodes 
                           if graph.in_degree[acc] + graph.out_degree[acc] >= self.fan_threshold]
        
        if len(high_degree_nodes) < 2:
            return patterns
        
        # Try to find bipartite structure
        # Group 1: Accounts that primarily send
        # Group 2: Accounts that primarily receive
        group1 = set()
        group2 = set()
        
        for account in graph.nodes:
            if graph.out_degree[account] > graph.in_degree[account] * 1.5:
                group1.add(account)
            elif graph.in_degree[account] > graph.out_degree[account] * 1.5:
                group2.add(account)
        
        # Check if there are many cross-group transactions
        cross_edges = 0
        for (from_acc, to_acc), txs in graph.edges.items():
            if (from_acc in group1 and to_acc in group2) or \
               (from_acc in group2 and to_acc in group1):
                cross_edges += len(txs)
        
        if len(group1) >= 2 and len(group2) >= 2 and cross_edges >= self.fan_threshold:
            all_accounts = list(group1) + list(group2)
            all_txs = []
            total_amount = 0.0
            
            for (from_acc, to_acc), txs in graph.edges.items():
                if (from_acc in group1 and to_acc in group2) or \
                   (from_acc in group2 and to_acc in group1):
                    for tx in txs:
                        all_txs.append(tx.get("transaction_id", ""))
                        total_amount += float(tx.get("amount", 0))
            
            severity = "high" if cross_edges >= 20 else "medium"
            confidence = min(1.0, cross_edges / 30.0)
            
            patterns.append(PatternMatch(
                pattern_type="bipartite",
                severity=severity,
                description=f"Bipartite pattern: Two distinct groups ({len(group1)} and {len(group2)} accounts) with {cross_edges} cross-group transactions",
                accounts_involved=all_accounts,
                transactions_involved=all_txs[:50],
                total_amount=total_amount,
                time_window_days=30,
                confidence=confidence,
                metadata={
                    "group1_size": len(group1),
                    "group2_size": len(group2),
                    "cross_edges": cross_edges
                }
            ))
        
        return patterns
    
    def _detect_layered_structure(self, graph: TransactionGraph) -> List[PatternMatch]:
        """Detect stack/layered structure: Multi-layer transaction flow."""
        patterns = []
        
        # Find accounts that act as intermediaries (receive and send)
        intermediaries = []
        for account in graph.nodes:
            if graph.in_degree[account] >= 2 and graph.out_degree[account] >= 2:
                intermediaries.append(account)
        
        if len(intermediaries) < 3:
            return patterns  # Need multiple layers
        
        # Group intermediaries by their position in the flow
        # Layer 1: High in-degree, low out-degree (sinks)
        # Layer 2: Balanced (intermediaries)
        # Layer 3: Low in-degree, high out-degree (sources)
        
        layers = {
            "source": [],
            "intermediate": [],
            "sink": []
        }
        
        for account in graph.nodes:
            in_deg = graph.in_degree[account]
            out_deg = graph.out_degree[account]
            
            if in_deg == 0 or (out_deg > in_deg * 2):
                layers["source"].append(account)
            elif out_deg == 0 or (in_deg > out_deg * 2):
                layers["sink"].append(account)
            elif in_deg >= 2 and out_deg >= 2:
                layers["intermediate"].append(account)
        
        # Check if we have a layered structure
        if len(layers["source"]) >= 2 and len(layers["intermediate"]) >= 2 and len(layers["sink"]) >= 1:
            all_accounts = layers["source"] + layers["intermediate"] + layers["sink"]
            all_txs = []
            total_amount = 0.0
            
            for (from_acc, to_acc), txs in graph.edges.items():
                if from_acc in all_accounts and to_acc in all_accounts:
                    for tx in txs:
                        all_txs.append(tx.get("transaction_id", ""))
                        total_amount += float(tx.get("amount", 0))
            
            total_layers = sum(len(l) for l in layers.values())
            severity = "high" if total_layers >= 10 else "medium"
            confidence = min(1.0, total_layers / 20.0)
            
            patterns.append(PatternMatch(
                pattern_type="layered",
                severity=severity,
                description=f"Layered structure: {len(layers['source'])} source accounts -> {len(layers['intermediate'])} intermediaries -> {len(layers['sink'])} sink accounts",
                accounts_involved=all_accounts,
                transactions_involved=all_txs[:50],
                total_amount=total_amount,
                time_window_days=30,
                confidence=confidence,
                metadata={
                    "source_count": len(layers["source"]),
                    "intermediate_count": len(layers["intermediate"]),
                    "sink_count": len(layers["sink"])
                }
            ))
        
        return patterns
    
    def _detect_random_graph(self, graph: TransactionGraph) -> List[PatternMatch]:
        """Detect random/complex graph structure: High connectivity, no clear pattern."""
        patterns = []
        
        # Calculate graph metrics
        total_nodes = len(graph.nodes)
        total_edges = len(graph.edges)
        
        if total_nodes < 5:
            return patterns
        
        # Calculate average degree
        avg_degree = sum(graph.in_degree[acc] + graph.out_degree[acc] for acc in graph.nodes) / total_nodes
        
        # Random graph indicator: High connectivity, many cycles, complex structure
        if avg_degree >= 3 and total_edges >= total_nodes * 1.5:
            # Check for high clustering (many triangles/cycles)
            cycle_count = 0
            for account in graph.nodes:
                neighbors = set(graph.get_neighbors(account, "out")) | set(graph.get_neighbors(account, "in"))
                # Count triangles
                for n1 in neighbors:
                    for n2 in neighbors:
                        if n1 != n2:
                            if (n1, n2) in graph.edges or (n2, n1) in graph.edges:
                                cycle_count += 1
            
            if cycle_count >= total_nodes:
                all_accounts = list(graph.nodes)
                all_txs = []
                total_amount = 0.0
                
                for (from_acc, to_acc), txs in graph.edges.items():
                    for tx in txs:
                        all_txs.append(tx.get("transaction_id", ""))
                        total_amount += float(tx.get("amount", 0))
                
                severity = "high" if avg_degree >= 5 else "medium"
                confidence = min(1.0, avg_degree / 10.0)
                
                patterns.append(PatternMatch(
                    pattern_type="random_graph",
                    severity=severity,
                    description=f"Random/complex graph structure: {total_nodes} accounts with {total_edges} transaction paths, average degree {avg_degree:.1f}",
                    accounts_involved=all_accounts[:100],  # Limit accounts
                    transactions_involved=all_txs[:100],
                    total_amount=total_amount,
                    time_window_days=30,
                    confidence=confidence,
                    metadata={
                        "node_count": total_nodes,
                        "edge_count": total_edges,
                        "avg_degree": avg_degree,
                        "cycle_indicators": cycle_count
                    }
                ))
        
        return patterns

