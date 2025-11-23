"""
PDF Report Generator - Generates comprehensive AML analysis reports with visualizations.
"""

import logging
import io
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import networkx as nx
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
import numpy as np

logger = logging.getLogger(__name__)


class PDFReportGenerator:
    """Generates PDF reports with AML analysis and visualizations."""
    
    def __init__(self, llm_service=None):
        """
        Initialize PDF report generator.
        
        Args:
            llm_service: Optional LLM service for generating text content
        """
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
        self.llm_service = llm_service
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles."""
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=30,
            alignment=TA_CENTER
        ))
        
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=12,
            spaceBefore=12
        ))
        
        self.styles.add(ParagraphStyle(
            name='RiskHigh',
            parent=self.styles['Normal'],
            textColor=colors.HexColor('#c0392b'),
            fontSize=12,
            fontName='Helvetica-Bold'
        ))
        
        self.styles.add(ParagraphStyle(
            name='RiskMedium',
            parent=self.styles['Normal'],
            textColor=colors.HexColor('#f39c12'),
            fontSize=12,
            fontName='Helvetica-Bold'
        ))
        
        self.styles.add(ParagraphStyle(
            name='RiskLow',
            parent=self.styles['Normal'],
            textColor=colors.HexColor('#27ae60'),
            fontSize=12
        ))
    
    def generate_report(
        self,
        output_path: str,
        accounts: List[Dict[str, Any]],
        transactions: List[Dict[str, Any]],
        patterns: List[Dict[str, Any]],
        risk_assessment: Dict[str, Any],
        pattern_explanations: List[Dict[str, Any]],
        temp_dir: str = "/tmp"
    ) -> str:
        """
        Generate comprehensive AML analysis PDF report.
        
        Args:
            output_path: Path to save PDF file
            accounts: List of accounts
            transactions: List of transactions
            patterns: Detected AML patterns
            risk_assessment: Overall risk assessment
            pattern_explanations: Pattern explanations with AML context
            temp_dir: Temporary directory for images
            
        Returns:
            Path to generated PDF file
        """
        doc = SimpleDocTemplate(output_path, pagesize=A4)
        story = []
        
        # Title page
        story.extend(self._create_title_page(risk_assessment))
        story.append(PageBreak())
        
        # Executive summary
        story.extend(self._create_executive_summary(risk_assessment, patterns))
        story.append(PageBreak())
        
        # Data overview
        story.extend(self._create_data_overview(accounts, transactions))
        story.append(PageBreak())
        
        # Pattern detections
        story.extend(self._create_pattern_detections(patterns, pattern_explanations))
        story.append(PageBreak())
        
        # Visualizations
        story.extend(self._create_visualizations(
            accounts, transactions, patterns, temp_dir
        ))
        
        # Build PDF
        doc.build(story)
        logger.info(f"PDF report generated: {output_path}")
        
        return output_path
    
    def _create_title_page(self, risk_assessment: Dict[str, Any]) -> List:
        """Create title page."""
        elements = []
        
        elements.append(Spacer(1, 2*inch))
        elements.append(Paragraph("AML Compliance Analysis Report", self.styles['CustomTitle']))
        elements.append(Spacer(1, 0.5*inch))
        
        elements.append(Paragraph(
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            self.styles['Normal']
        ))
        elements.append(Spacer(1, 1*inch))
        
        # Risk level
        risk_level = risk_assessment.get("overall_risk", "unknown").upper()
        risk_style = self._get_risk_style(risk_level)
        elements.append(Paragraph(
            f"Overall Risk Level: {risk_level}",
            risk_style
        ))
        elements.append(Spacer(1, 0.3*inch))
        
        elements.append(Paragraph(
            risk_assessment.get("summary", ""),
            self.styles['Normal']
        ))
        
        return elements
    
    def _create_executive_summary(self, risk_assessment: Dict[str, Any], patterns: List[Dict[str, Any]]) -> List:
        """Create executive summary section using LLM if available."""
        elements = []
        
        elements.append(Paragraph("Executive Summary", self.styles['SectionHeader']))
        elements.append(Spacer(1, 0.2*inch))
        
        # Generate summary with LLM if available
        if self.llm_service:
            try:
                risk_level = risk_assessment.get("overall_risk", "unknown").upper()
                num_patterns = len(patterns)
                pattern_types = ', '.join(set(p.get('pattern_type', 'unknown').replace('_', ' ').title() for p in patterns[:10]))
                
                prompt = f"""Generate a professional executive summary for an AML compliance analysis report.

Risk Level: {risk_level}
Number of Patterns Detected: {num_patterns}
Recommendation: {risk_assessment.get('recommendation', 'N/A')}
Pattern Types Found: {pattern_types}

Write a concise executive summary (2-3 paragraphs) that:
1. States the overall risk assessment
2. Summarizes key findings
3. Provides actionable recommendations
4. Uses professional compliance language

Executive Summary:"""
                
                summary_text = self.llm_service.generate(prompt, max_new_tokens=300, temperature=0.3)
                elements.append(Paragraph(summary_text, self.styles['Normal']))
                logger.info("Generated executive summary using LLM")
            except Exception as e:
                logger.warning(f"LLM summary generation failed: {e}, using fallback")
                summary_text = self._get_fallback_summary(risk_assessment, patterns)
                elements.append(Paragraph(summary_text, self.styles['Normal']))
        else:
            summary_text = self._get_fallback_summary(risk_assessment, patterns)
            elements.append(Paragraph(summary_text, self.styles['Normal']))
        
        return elements
    
    def _get_fallback_summary(self, risk_assessment: Dict[str, Any], patterns: List[Dict[str, Any]]) -> str:
        """Fallback summary if LLM is not available."""
        risk_level = risk_assessment.get("overall_risk", "unknown").upper()
        num_patterns = len(patterns)
        return f"""
        This report presents the results of an automated AML (Anti-Money Laundering) 
        pattern detection analysis conducted on the provided transaction data. The analysis 
        utilized graph-based algorithms to identify known money laundering typologies 
        as defined by FINMA regulations.
        
        Overall risk level: <b>{risk_level}</b>. Analysis detected <b>{num_patterns}</b> potential 
        AML laundering patterns requiring further investigation.
        """
    
    def _create_data_overview(self, accounts: List[Dict[str, Any]], transactions: List[Dict[str, Any]]) -> List:
        """Create data overview section."""
        elements = []
        
        elements.append(Paragraph("Data Overview", self.styles['SectionHeader']))
        elements.append(Spacer(1, 0.2*inch))
        
        # Statistics
        total_amount = sum(tx.get("amount", 0) for tx in transactions)
        unique_accounts = len(set(
            [tx.get("from_account") for tx in transactions] +
            [tx.get("to_account") for tx in transactions]
        ))
        
        stats_data = [
            ["Metric", "Value"],
            ["Total Accounts", len(accounts)],
            ["Unique Accounts in Transactions", unique_accounts],
            ["Total Transactions", len(transactions)],
            ["Total Transaction Volume", f"{total_amount:,.2f}"],
            ["Average Transaction Amount", f"{total_amount/len(transactions) if transactions else 0:,.2f}"],
        ]
        
        table = Table(stats_data, colWidths=[3*inch, 2*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(table)
        
        return elements
    
    def _create_pattern_detections(self, patterns: List[Dict[str, Any]], explanations: List[Dict[str, Any]]) -> List:
        """Create pattern detections section."""
        elements = []
        
        elements.append(Paragraph("Detected AML Patterns", self.styles['SectionHeader']))
        elements.append(Spacer(1, 0.2*inch))
        
        if not patterns:
            elements.append(Paragraph(
                "No known AML patterns detected in the transaction data.",
                self.styles['Normal']
            ))
            return elements
        
        # Group explanations by pattern type
        explanations_dict = {}
        for exp in explanations:
            ptype = exp.get("pattern_type", "unknown")
            if ptype not in explanations_dict:
                explanations_dict[ptype] = []
            explanations_dict[ptype].append(exp)
        
        for i, pattern in enumerate(patterns[:20], 1):  # Limit to first 20
            pattern_type = pattern.get("pattern_type", "unknown")
            # Get first explanation of this type
            explanation = explanations_dict.get(pattern_type, [{}])[0] if explanations_dict.get(pattern_type) else {}
            
            # Pattern header
            severity = pattern.get("severity", "low").upper()
            risk_style = self._get_risk_style(severity)
            
            elements.append(Paragraph(
                f"Pattern {i}: {pattern_type.replace('_', ' ').title()} - {severity} Risk",
                risk_style
            ))
            elements.append(Spacer(1, 0.1*inch))
            
            # Description
            elements.append(Paragraph(
                f"<b>Description:</b> {pattern.get('description', 'N/A')}",
                self.styles['Normal']
            ))
            elements.append(Spacer(1, 0.1*inch))
            
            # AML Context - generate with LLM if available
            if explanation:
                if self.llm_service:
                    try:
                        pattern_explanation = self._generate_pattern_explanation_with_llm(pattern, explanation)
                        elements.append(Paragraph(pattern_explanation, self.styles['Normal']))
                        elements.append(Spacer(1, 0.1*inch))
                    except Exception as e:
                        logger.warning(f"LLM pattern explanation failed: {e}, using fallback")
                        self._add_fallback_explanation(elements, explanation)
                else:
                    self._add_fallback_explanation(elements, explanation)
            
            # Details
            details = [
                f"Accounts involved: {len(pattern.get('accounts_involved', []))}",
                f"Transactions involved: {len(pattern.get('transactions_involved', []))}",
                f"Total amount: {pattern.get('total_amount', 0):,.2f}",
                f"Confidence: {pattern.get('confidence', 0):.1%}"
            ]
            
            for detail in details:
                elements.append(Paragraph(f"• {detail}", self.styles['Normal']))
            
            # Compliance implications
            if explanation and explanation.get("compliance_implications"):
                elements.append(Spacer(1, 0.1*inch))
                elements.append(Paragraph("<b>Compliance Implications:</b>", self.styles['Normal']))
                for impl in explanation["compliance_implications"][:3]:  # Limit to 3
                    elements.append(Paragraph(f"• {impl}", self.styles['Normal']))
            
            # Recommended actions
            if explanation and explanation.get("recommended_actions"):
                elements.append(Spacer(1, 0.1*inch))
                elements.append(Paragraph("<b>Recommended Actions:</b>", self.styles['Normal']))
                for action in explanation["recommended_actions"][:3]:  # Limit to 3
                    elements.append(Paragraph(f"• {action}", self.styles['Normal']))
            
            elements.append(Spacer(1, 0.3*inch))
        
        return elements
    
    def _generate_pattern_explanation_with_llm(self, pattern: Dict[str, Any], explanation: Dict[str, Any]) -> str:
        """Generate pattern explanation using LLM."""
        pattern_type = pattern.get("pattern_type", "unknown")
        severity = pattern.get("severity", "medium")
        accounts_involved = pattern.get("accounts_involved", [])[:5]
        total_amount = pattern.get("total_amount", 0)
        
        prompt = f"""Explain this AML pattern detection in a professional compliance report format.

Pattern Type: {pattern_type.replace('_', ' ').title()}
Severity: {severity.upper()}
Accounts Involved: {', '.join(accounts_involved)}
Total Amount: {total_amount:,.2f}

AML Context: {explanation.get('aml_context', explanation.get('explanation', 'N/A'))}
Regulatory Basis: {explanation.get('regulatory_basis', 'N/A')}
Compliance Implications: {explanation.get('compliance_implications', 'N/A')}
Recommended Actions: {explanation.get('recommended_actions', 'N/A')}

Write a comprehensive explanation (2-3 paragraphs) that:
1. Explains what this pattern indicates in AML terms
2. Describes the compliance implications based on FINMA regulations
3. Provides specific recommended actions
4. Uses professional compliance language

Do NOT claim criminal intent - only describe suspicious activity patterns.

Explanation:"""
        
        explanation_text = self.llm_service.generate(prompt, max_new_tokens=400, temperature=0.3)
        return f"<b>AML Analysis:</b> {explanation_text}"
    
    def _add_fallback_explanation(self, elements: List, explanation: Dict[str, Any]):
        """Add fallback explanation without LLM."""
        elements.append(Paragraph(
            f"<b>AML Context:</b> {explanation.get('explanation', explanation.get('aml_context', 'N/A'))}",
            self.styles['Normal']
        ))
        elements.append(Spacer(1, 0.1*inch))
        
        elements.append(Paragraph(
            f"<b>Regulatory Basis:</b> {explanation.get('regulatory_basis', 'N/A')}",
            self.styles['Normal']
        ))
        elements.append(Spacer(1, 0.1*inch))
        
        if explanation.get("compliance_implications"):
            elements.append(Paragraph("<b>Compliance Implications:</b>", self.styles['Normal']))
            for impl in explanation["compliance_implications"][:3]:
                elements.append(Paragraph(f"• {impl}", self.styles['Normal']))
            elements.append(Spacer(1, 0.1*inch))
        
        if explanation.get("recommended_actions"):
            elements.append(Paragraph("<b>Recommended Actions:</b>", self.styles['Normal']))
            for impl in explanation["recommended_actions"][:3]:
                elements.append(Paragraph(f"• {impl}", self.styles['Normal']))
    
    def _create_visualizations(
        self,
        accounts: List[Dict[str, Any]],
        transactions: List[Dict[str, Any]],
        patterns: List[Dict[str, Any]],
        temp_dir: str
    ) -> List:
        """Create visualization section."""
        elements = []
        
        elements.append(Paragraph("Visualizations", self.styles['SectionHeader']))
        elements.append(Spacer(1, 0.2*inch))
        
        # Create visualizations
        temp_path = Path(temp_dir)
        temp_path.mkdir(parents=True, exist_ok=True)
        
        # 1. Transaction network graph
        network_img = self._create_network_graph(accounts, transactions, patterns, temp_path / "network.png")
        if network_img:
            elements.append(Paragraph("Transaction Network Graph", self.styles['Heading3']))
            elements.append(Spacer(1, 0.1*inch))
            elements.append(Image(network_img, width=6*inch, height=4.5*inch))
            elements.append(Spacer(1, 0.3*inch))
        
        # 2. Pattern-highlighted subgraph
        pattern_img = self._create_pattern_subgraph(transactions, patterns, temp_path / "patterns.png")
        if pattern_img:
            elements.append(Paragraph("Pattern-Highlighted Subgraph", self.styles['Heading3']))
            elements.append(Spacer(1, 0.1*inch))
            elements.append(Image(pattern_img, width=6*inch, height=4.5*inch))
            elements.append(Spacer(1, 0.3*inch))
        
        # 3. Flow diagram
        flow_img = self._create_flow_diagram(transactions, patterns, temp_path / "flow.png")
        if flow_img:
            elements.append(Paragraph("Fund Flow Diagram", self.styles['Heading3']))
            elements.append(Spacer(1, 0.1*inch))
            elements.append(Image(flow_img, width=6*inch, height=4.5*inch))
            elements.append(Spacer(1, 0.3*inch))
        
        # 4. Risk heatmap
        heatmap_img = self._create_risk_heatmap(accounts, transactions, patterns, temp_path / "heatmap.png")
        if heatmap_img:
            elements.append(Paragraph("Risk Heatmap", self.styles['Heading3']))
            elements.append(Spacer(1, 0.1*inch))
            elements.append(Image(heatmap_img, width=6*inch, height=4.5*inch))
        
        return elements
    
    def _create_network_graph(
        self,
        accounts: List[Dict[str, Any]],
        transactions: List[Dict[str, Any]],
        patterns: List[Dict[str, Any]],
        output_path: Path
    ) -> Optional[str]:
        """Create transaction network graph visualization."""
        try:
            G = nx.DiGraph()
            
            # Add nodes and edges
            for tx in transactions[:500]:  # Limit for visualization
                from_acc = tx.get("from_account", "")
                to_acc = tx.get("to_account", "")
                if from_acc and to_acc:
                    G.add_edge(from_acc, to_acc, weight=tx.get("amount", 0))
            
            if len(G.nodes()) == 0:
                return None
            
            # Use spring layout
            pos = nx.spring_layout(G, k=0.5, iterations=50)
            
            plt.figure(figsize=(12, 9))
            
            # Draw edges
            nx.draw_networkx_edges(G, pos, alpha=0.3, width=0.5, arrows=True, arrowsize=10)
            
            # Draw nodes
            node_sizes = [G.degree(node) * 100 for node in G.nodes()]
            nx.draw_networkx_nodes(G, pos, node_size=node_sizes, node_color='lightblue', alpha=0.7)
            
            # Draw labels for high-degree nodes only
            high_degree_nodes = [n for n in G.nodes() if G.degree(n) > 5]
            labels = {n: n[:8] + "..." if len(n) > 8 else n for n in high_degree_nodes}
            nx.draw_networkx_labels(G, pos, labels, font_size=8)
            
            plt.title("Transaction Network Graph\n(Nodes = Accounts, Edges = Transactions)", fontsize=14)
            plt.axis('off')
            plt.tight_layout()
            plt.savefig(output_path, dpi=150, bbox_inches='tight')
            plt.close()
            
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Error creating network graph: {e}")
            return None
    
    def _create_pattern_subgraph(
        self,
        transactions: List[Dict[str, Any]],
        patterns: List[Dict[str, Any]],
        output_path: Path
    ) -> Optional[str]:
        """Create pattern-highlighted subgraph."""
        try:
            if not patterns:
                return None
            
            G = nx.DiGraph()
            
            # Get accounts from high-severity patterns
            high_severity_patterns = [p for p in patterns if p.get("severity") == "high"][:5]
            
            pattern_accounts = set()
            for pattern in high_severity_patterns:
                pattern_accounts.update(pattern.get("accounts_involved", [])[:20])
            
            # Add edges for pattern accounts
            for tx in transactions:
                from_acc = tx.get("from_account", "")
                to_acc = tx.get("to_account", "")
                if from_acc in pattern_accounts and to_acc in pattern_accounts:
                    G.add_edge(from_acc, to_acc, weight=tx.get("amount", 0))
            
            if len(G.nodes()) == 0:
                return None
            
            pos = nx.spring_layout(G, k=1, iterations=50)
            
            plt.figure(figsize=(12, 9))
            
            # Draw edges
            nx.draw_networkx_edges(G, pos, alpha=0.5, width=1, arrows=True, arrowsize=15, edge_color='red')
            
            # Draw nodes
            nx.draw_networkx_nodes(G, pos, node_size=500, node_color='red', alpha=0.7)
            
            # Draw labels
            labels = {n: n[:10] + "..." if len(n) > 10 else n for n in G.nodes()}
            nx.draw_networkx_labels(G, pos, labels, font_size=8)
            
            plt.title("Pattern-Highlighted Subgraph\n(High-Risk Patterns Circled)", fontsize=14)
            plt.axis('off')
            plt.tight_layout()
            plt.savefig(output_path, dpi=150, bbox_inches='tight')
            plt.close()
            
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Error creating pattern subgraph: {e}")
            return None
    
    def _create_flow_diagram(
        self,
        transactions: List[Dict[str, Any]],
        patterns: List[Dict[str, Any]],
        output_path: Path
    ) -> Optional[str]:
        """Create fund flow diagram."""
        try:
            # Calculate flow for top accounts
            account_flows = {}
            for tx in transactions:
                from_acc = tx.get("from_account", "")
                to_acc = tx.get("to_account", "")
                amount = tx.get("amount", 0)
                
                if from_acc:
                    account_flows[from_acc] = account_flows.get(from_acc, 0) - amount
                if to_acc:
                    account_flows[to_acc] = account_flows.get(to_acc, 0) + amount
            
            # Get top accounts by flow
            sorted_accounts = sorted(account_flows.items(), key=lambda x: abs(x[1]), reverse=True)[:10]
            
            if not sorted_accounts:
                return None
            
            fig, ax = plt.subplots(figsize=(12, 6))
            
            accounts = [acc[:15] + "..." if len(acc) > 15 else acc for acc, _ in sorted_accounts]
            flows = [flow for _, flow in sorted_accounts]
            
            colors_list = ['red' if f < 0 else 'green' for f in flows]
            
            bars = ax.barh(accounts, flows, color=colors_list, alpha=0.7)
            ax.set_xlabel('Net Flow Amount', fontsize=12)
            ax.set_title('Fund Flow Diagram\n(Top Accounts by Net Flow)', fontsize=14)
            ax.axvline(x=0, color='black', linestyle='--', linewidth=1)
            ax.grid(axis='x', alpha=0.3)
            
            plt.tight_layout()
            plt.savefig(output_path, dpi=150, bbox_inches='tight')
            plt.close()
            
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Error creating flow diagram: {e}")
            return None
    
    def _create_risk_heatmap(
        self,
        accounts: List[Dict[str, Any]],
        transactions: List[Dict[str, Any]],
        patterns: List[Dict[str, Any]],
        output_path: Path
    ) -> Optional[str]:
        """Create risk heatmap."""
        try:
            # Calculate risk scores for accounts
            account_risk = {}
            
            for pattern in patterns:
                severity_score = {"high": 3, "medium": 2, "low": 1}.get(pattern.get("severity", "low"), 0)
                for account in pattern.get("accounts_involved", []):
                    account_risk[account] = account_risk.get(account, 0) + severity_score
            
            if not account_risk:
                return None
            
            # Get top risky accounts
            sorted_risks = sorted(account_risk.items(), key=lambda x: x[1], reverse=True)[:15]
            
            accounts_list = [acc[:20] + "..." if len(acc) > 20 else acc for acc, _ in sorted_risks]
            risk_scores = [score for _, score in sorted_risks]
            
            fig, ax = plt.subplots(figsize=(10, 8))
            
            # Create heatmap
            risk_matrix = np.array(risk_scores).reshape(-1, 1)
            im = ax.imshow(risk_matrix, cmap='Reds', aspect='auto')
            
            # Set labels
            ax.set_xticks([0])
            ax.set_xticklabels(['Risk Score'])
            ax.set_yticks(range(len(accounts_list)))
            ax.set_yticklabels(accounts_list, fontsize=8)
            
            # Add text annotations
            for i, score in enumerate(risk_scores):
                ax.text(0, i, f'{score}', ha='center', va='center', color='white' if score > 5 else 'black', fontweight='bold')
            
            ax.set_title('Risk Heatmap\n(Accounts with Highest Suspicious Activity)', fontsize=14)
            plt.colorbar(im, ax=ax, label='Risk Score')
            plt.tight_layout()
            plt.savefig(output_path, dpi=150, bbox_inches='tight')
            plt.close()
            
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Error creating risk heatmap: {e}")
            return None
    
    def _get_risk_style(self, risk_level: str) -> ParagraphStyle:
        """Get paragraph style based on risk level."""
        risk_lower = risk_level.lower()
        if "high" in risk_lower or "critical" in risk_lower:
            return self.styles['RiskHigh']
        elif "medium" in risk_lower:
            return self.styles['RiskMedium']
        else:
            return self.styles['RiskLow']

