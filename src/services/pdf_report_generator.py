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
        
        self.styles.add(ParagraphStyle(
            name='Highlight',
            parent=self.styles['Normal'],
            textColor=colors.HexColor('#c0392b'),
            backColor=colors.HexColor('#ffe6e6'),
            fontSize=10,
            fontName='Helvetica-Bold'
        ))
        
        self.styles.add(ParagraphStyle(
            name='Warning',
            parent=self.styles['Normal'],
            textColor=colors.HexColor('#f39c12'),
            fontSize=10,
            fontName='Helvetica-Bold'
        ))
    
    def generate_report(
        self,
        output_path: str,
        accounts: List[Dict[str, Any]],
        transactions: List[Dict[str, Any]],
        patterns: List[Dict[str, Any]],
        risk_assessment: Dict[str, Any],
        pattern_explanations: List[Dict[str, Any]],
        temp_dir: str = "/tmp",
        generated_by: str = "System",
        filename: str = "upload.xlsx"
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
            generated_by: Name of officer who generated the report
            filename: Name of uploaded file
            
        Returns:
            Path to generated PDF file
        """
        doc = SimpleDocTemplate(output_path, pagesize=A4)
        story = []
        
        # Title page
        story.extend(self._create_title_page(risk_assessment, generated_by, filename))
        story.append(PageBreak())
        
        # Table of Contents
        story.extend(self._create_table_of_contents(patterns))
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
        
        # Visual Evidence Section - NEW!
        story.extend(self._create_visual_evidence_section(
            transactions, patterns, accounts
        ))
        story.append(PageBreak())
        
        # Visualizations
        story.extend(self._create_visualizations(
            accounts, transactions, patterns, temp_dir
        ))
        
        # Build PDF
        doc.build(story)
        logger.info(f"PDF report generated: {output_path}")
        
        return output_path
    
    def _create_title_page(
        self,
        risk_assessment: Dict[str, Any],
        generated_by: str = "System",
        filename: str = "upload.xlsx"
    ) -> List:
        """Create title page with officer info and timestamp."""
        elements = []
        
        # Title
        elements.append(Spacer(1, 1.5*inch))
        elements.append(Paragraph(
            "AML COMPLIANCE ANALYSIS REPORT",
            self.styles['CustomTitle']
        ))
        elements.append(Spacer(1, 0.5*inch))
        
        # Risk badge
        risk_level = risk_assessment.get("overall_risk", "unknown").upper()
        risk_style = self._get_risk_style(risk_level)
        elements.append(Paragraph(
            f"RISK LEVEL: {risk_level}",
            risk_style
        ))
        elements.append(Spacer(1, 0.8*inch))
        
        # Report metadata table
        report_date = datetime.now().strftime("%B %d, %Y")
        report_time = datetime.now().strftime("%H:%M:%S")
        
        metadata_data = [
            ["Report Information", ""],
            ["Generated By:", f"Officer {generated_by}"],
            ["Date:", report_date],
            ["Time:", report_time],
            ["Source File:", filename],
        ]
        
        metadata_table = Table(metadata_data, colWidths=[2*inch, 3.5*inch])
        metadata_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#ecf0f1')),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        elements.append(metadata_table)
        elements.append(Spacer(1, 0.8*inch))
        
        # Confidentiality notice
        elements.append(Paragraph(
            "<b>CONFIDENTIAL - For Internal Use Only</b>",
            self.styles['Normal']
        ))
        elements.append(Spacer(1, 0.2*inch))
        elements.append(Paragraph(
            "This report contains sensitive AML analysis and should be handled in accordance with "
            "data protection regulations and internal compliance procedures.",
            self.styles['Normal']
        ))
        
        return elements
    
    def _create_table_of_contents(self, patterns: List[Dict[str, Any]]) -> List:
        """Create table of contents as plain text."""
        elements = []
        
        elements.append(Paragraph("Table of Contents", self.styles['CustomTitle']))
        elements.append(Spacer(1, 0.5*inch))
        
        # Create TOC as paragraphs instead of table
        toc_items = [
            "<b>1. Executive Summary</b>",
            "   Overview of findings and risk assessment",
            "",
            "<b>2. Data Overview</b>",
            "   Transaction and account statistics",
            "",
            "<b>3. Pattern Detections</b>",
            f"   Detailed analysis of {len(patterns)} AML patterns identified",
            "",
            "<b>4. Visual Evidence</b>",
            "   • Suspicious Transactions (highlighted)",
            "   • High-Risk Counterparties",
            "   • Red Flag Summary",
            "",
            "<b>5. Visualizations & Charts</b>",
            "   • Red Flags Distribution Pie Chart",
            "   • SAR Filing Recommendation Pie Chart",
            "   • Highest Risk Account Spider Chart",
        ]
        
        for item in toc_items:
            if item == "":
                elements.append(Spacer(1, 0.1*inch))
            else:
                elements.append(Paragraph(item, self.styles['Normal']))
        
        elements.append(Spacer(1, 0.3*inch))
        
        # Horizontal line separator
        elements.append(Spacer(1, 0.2*inch))
        
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
    
    def _create_visual_evidence_section(
        self,
        transactions: List[Dict[str, Any]],
        patterns: List[Dict[str, Any]],
        accounts: List[Dict[str, Any]]
    ) -> List:
        """
        Create visual evidence section showing which data fields influenced conclusions.
        Highlights suspicious transactions, high-risk counterparties, and red flag indicators.
        """
        elements = []
        
        elements.append(Paragraph(
            "🔍 Visual Evidence - What Triggered the Alerts",
            self.styles['SectionHeader']
        ))
        elements.append(Spacer(1, 0.2*inch))
        
        elements.append(Paragraph(
            "This section visually highlights the specific data points that influenced the risk assessment. "
            "Red highlighting indicates high-risk elements, yellow indicates medium-risk warnings.",
            self.styles['Normal']
        ))
        elements.append(Spacer(1, 0.3*inch))
        
        # Get suspicious transaction IDs from patterns
        suspicious_tx_ids = set()
        high_risk_accounts = set()
        
        for pattern in patterns:
            suspicious_tx_ids.update(pattern.get('transactions_involved', []))
            high_risk_accounts.update(pattern.get('accounts_involved', []))
        
        # 1. Highlighted Transactions Table
        elements.extend(self._create_highlighted_transactions_table(
            transactions, suspicious_tx_ids, high_risk_accounts
        ))
        
        # 2. High-Risk Counterparties Summary
        elements.extend(self._create_high_risk_counterparties_section(
            accounts, high_risk_accounts, patterns
        ))
        
        # 3. Red Flag Indicators
        elements.extend(self._create_red_flag_indicators(patterns))
        
        return elements
    
    def _create_highlighted_transactions_table(
        self,
        transactions: List[Dict[str, Any]],
        suspicious_tx_ids: set,
        high_risk_accounts: set
    ) -> List:
        """Create table with highlighted suspicious transactions."""
        elements = []
        
        elements.append(Paragraph(
            "🚨 Suspicious Transactions (Highlighted in Red)",
            self.styles['Heading3']
        ))
        elements.append(Spacer(1, 0.1*inch))
        
        # Filter to only suspicious transactions (limit to 15 for readability)
        suspicious_txs = [
            tx for tx in transactions
            if tx.get('transaction_id') in suspicious_tx_ids
        ][:15]
        
        if not suspicious_txs:
            elements.append(Paragraph("No specific transactions flagged.", self.styles['Normal']))
            elements.append(Spacer(1, 0.2*inch))
            return elements
        
        # Build table data
        table_data = [["TX ID", "From → To", "Amount", "Risk Indicator"]]
        
        for tx in suspicious_txs:
            tx_id = str(tx.get('transaction_id', 'N/A'))[:10]
            from_acc = str(tx.get('from_account', 'N/A'))[:12]
            to_acc = str(tx.get('to_account', 'N/A'))[:12]
            amount = tx.get('amount', 0)
            
            # Determine risk indicators - use shorter text
            indicators = []
            if from_acc in high_risk_accounts or to_acc in high_risk_accounts:
                indicators.append("High-Risk Acc")
            if amount >= 9500 and amount < 10000:
                indicators.append("Under Threshold")
            if amount >= 10000:
                indicators.append("Large Amount")
            
            risk_text = "\n".join(indicators) if indicators else "Suspicious\nPattern"
            
            table_data.append([
                tx_id,
                f"{from_acc}\n→ {to_acc}",
                f"{amount:,.2f}",
                risk_text
            ])
        
        # Create table with better column widths to prevent overflow
        table = Table(table_data, colWidths=[0.9*inch, 2.2*inch, 1*inch, 2.6*inch])
        
        # Table style with red background for suspicious rows
        style_commands = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('TOPPADDING', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('WORDWRAP', (0, 0), (-1, -1), True),
        ]
        
        # Highlight suspicious rows in red
        for i in range(1, len(table_data)):
            style_commands.append(('BACKGROUND', (0, i), (-1, i), colors.HexColor('#ffe6e6')))
            style_commands.append(('TEXTCOLOR', (0, i), (-1, i), colors.HexColor('#c0392b')))
            style_commands.append(('FONTNAME', (0, i), (-1, i), 'Helvetica-Bold'))
        
        table.setStyle(TableStyle(style_commands))
        elements.append(table)
        elements.append(Spacer(1, 0.3*inch))
        
        return elements
    
    def _create_high_risk_counterparties_section(
        self,
        accounts: List[Dict[str, Any]],
        high_risk_accounts: set,
        patterns: List[Dict[str, Any]]
    ) -> List:
        """Create section highlighting high-risk counterparties with danger icons."""
        elements = []
        
        elements.append(Paragraph(
            "⚠️ High-Risk Counterparties",
            self.styles['Heading3']
        ))
        elements.append(Spacer(1, 0.1*inch))
        
        if not high_risk_accounts:
            elements.append(Paragraph("No high-risk accounts identified.", self.styles['Normal']))
            elements.append(Spacer(1, 0.2*inch))
            return elements
        
        # Count patterns per account
        account_pattern_count = {}
        for pattern in patterns:
            for acc in pattern.get('accounts_involved', []):
                account_pattern_count[acc] = account_pattern_count.get(acc, 0) + 1
        
        # Sort by pattern count
        sorted_accounts = sorted(
            high_risk_accounts,
            key=lambda x: account_pattern_count.get(x, 0),
            reverse=True
        )[:10]  # Top 10
        
        table_data = [["🚨 Account ID", "Pattern Count", "Risk Level"]]
        
        for acc_id in sorted_accounts:
            count = account_pattern_count.get(acc_id, 0)
            risk_level = "CRITICAL" if count >= 3 else "HIGH" if count >= 2 else "MEDIUM"
            risk_icon = "🔴" if count >= 3 else "🟠" if count >= 2 else "🟡"
            
            table_data.append([
                str(acc_id)[:30],
                str(count),
                f"{risk_icon} {risk_level}"
            ])
        
        table = Table(table_data, colWidths=[3*inch, 1.5*inch, 1.5*inch])
        style_commands = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e74c3c')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]
        
        # Alternate row colors for critical accounts
        for i in range(1, len(table_data)):
            if "CRITICAL" in table_data[i][2]:
                style_commands.append(('BACKGROUND', (0, i), (-1, i), colors.HexColor('#ffcccc')))
            elif "HIGH" in table_data[i][2]:
                style_commands.append(('BACKGROUND', (0, i), (-1, i), colors.HexColor('#ffe6cc')))
            else:
                style_commands.append(('BACKGROUND', (0, i), (-1, i), colors.HexColor('#fff9e6')))
        
        table.setStyle(TableStyle(style_commands))
        elements.append(table)
        elements.append(Spacer(1, 0.3*inch))
        
        return elements
    
    def _create_red_flag_indicators(self, patterns: List[Dict[str, Any]]) -> List:
        """Create visual summary of red flag indicators."""
        elements = []
        
        elements.append(Paragraph(
            "🚩 Red Flag Summary",
            self.styles['Heading3']
        ))
        elements.append(Spacer(1, 0.1*inch))
        
        # Group patterns by type and severity
        high_risk_patterns = [p for p in patterns if p.get('severity') == 'high']
        medium_risk_patterns = [p for p in patterns if p.get('severity') == 'medium']
        
        # Create visual indicators
        if high_risk_patterns:
            elements.append(Paragraph(
                f"<b>🔴 CRITICAL FINDINGS ({len(high_risk_patterns)}):</b>",
                self.styles['RiskHigh']
            ))
            for pattern in high_risk_patterns[:5]:
                pattern_type = pattern.get('pattern_type', 'unknown').replace('_', ' ').title()
                elements.append(Paragraph(
                    f"• {pattern_type} - {pattern.get('description', 'N/A')}",
                    self.styles['Highlight']
                ))
            elements.append(Spacer(1, 0.2*inch))
        
        if medium_risk_patterns:
            elements.append(Paragraph(
                f"<b>🟠 MEDIUM RISK FINDINGS ({len(medium_risk_patterns)}):</b>",
                self.styles['RiskMedium']
            ))
            for pattern in medium_risk_patterns[:5]:
                pattern_type = pattern.get('pattern_type', 'unknown').replace('_', ' ').title()
                elements.append(Paragraph(
                    f"• {pattern_type} - {pattern.get('description', 'N/A')}",
                    self.styles['Warning']
                ))
            elements.append(Spacer(1, 0.2*inch))
        
        # Visual legend
        elements.append(Spacer(1, 0.2*inch))
        elements.append(Paragraph("<b>Legend:</b>", self.styles['Normal']))
        elements.append(Paragraph(
            "🔴 = Critical risk requiring immediate action | "
            "🟠 = Medium risk requiring review | "
            "🟡 = Low risk for monitoring | "
            "⚠️ = Warning indicator",
            self.styles['Normal']
        ))
        
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
        
        elements.append(Paragraph("Visualizations & Charts", self.styles['SectionHeader']))
        elements.append(Spacer(1, 0.2*inch))
        
        # Create visualizations
        temp_path = Path(temp_dir)
        temp_path.mkdir(parents=True, exist_ok=True)
        
        # 1. Red Flags Pie Chart (NEW!)
        red_flags_img = self._create_red_flags_pie_chart(patterns, temp_path / "red_flags_pie.png")
        if red_flags_img:
            elements.append(Paragraph("Red Flags Distribution", self.styles['Heading3']))
            elements.append(Spacer(1, 0.1*inch))
            elements.append(Image(red_flags_img, width=5*inch, height=4*inch))
            elements.append(Spacer(1, 0.3*inch))
        
        # 2. SAR Recommendation Pie Chart (NEW!)
        sar_img = self._create_sar_pie_chart(patterns, temp_path / "sar_pie.png")
        if sar_img:
            elements.append(Paragraph("SAR Filing Recommendation", self.styles['Heading3']))
            elements.append(Spacer(1, 0.1*inch))
            elements.append(Image(sar_img, width=5*inch, height=4*inch))
            elements.append(Spacer(1, 0.3*inch))
        
        # 3. Spider Web Chart - Highest Risk Account
        spider_img = self._create_spider_chart(patterns, temp_path / "spider.png")
        if spider_img:
            elements.append(Paragraph("Highest Risk Account - Pattern Analysis", self.styles['Heading3']))
            elements.append(Spacer(1, 0.1*inch))
            elements.append(Image(spider_img, width=5.5*inch, height=5.5*inch))
            elements.append(Spacer(1, 0.3*inch))
        
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
    
    def _create_red_flags_pie_chart(
        self,
        patterns: List[Dict[str, Any]],
        output_path: Path
    ) -> Optional[str]:
        """Create pie chart showing distribution of red flags by type."""
        try:
            if not patterns:
                return None
            
            # Count patterns by type
            pattern_counts = {}
            for pattern in patterns:
                pattern_type = pattern.get('pattern_type', 'unknown').replace('_', ' ').title()
                pattern_counts[pattern_type] = pattern_counts.get(pattern_type, 0) + 1
            
            if not pattern_counts:
                return None
            
            # Create pie chart
            fig, ax = plt.subplots(figsize=(10, 8))
            
            # Sort by count for better visualization
            sorted_items = sorted(pattern_counts.items(), key=lambda x: x[1], reverse=True)
            labels = [item[0] for item in sorted_items]
            sizes = [item[1] for item in sorted_items]
            
            # Color scheme - red shades for high risk
            colors_list = ['#e74c3c', '#c0392b', '#f39c12', '#e67e22', '#d35400', 
                          '#16a085', '#27ae60', '#2980b9', '#8e44ad', '#2c3e50']
            
            # Create pie chart with percentages
            wedges, texts, autotexts = ax.pie(
                sizes,
                labels=labels,
                autopct='%1.1f%%',
                startangle=90,
                colors=colors_list[:len(sizes)],
                textprops={'fontsize': 11, 'weight': 'bold'}
            )
            
            # Make percentage text more visible
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontsize(12)
                autotext.set_weight('bold')
            
            ax.set_title('Red Flags Distribution by Pattern Type', 
                        fontsize=16, weight='bold', pad=20)
            
            # Add legend with counts
            legend_labels = [f"{label}: {size}" for label, size in zip(labels, sizes)]
            ax.legend(legend_labels, loc='center left', bbox_to_anchor=(1, 0, 0.5, 1),
                     fontsize=10)
            
            plt.tight_layout()
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            return str(output_path)
        
        except Exception as e:
            logger.error(f"Error creating red flags pie chart: {e}")
            plt.close()
            return None
    
    def _create_sar_pie_chart(
        self,
        patterns: List[Dict[str, Any]],
        output_path: Path
    ) -> Optional[str]:
        """Create pie chart showing SAR filing recommendation breakdown."""
        try:
            if not patterns:
                # No patterns = No SAR
                labels = ['No SAR Filing Needed']
                sizes = [100]
                colors_list = ['#27ae60']
            else:
                # Categorize by severity
                high_risk = sum(1 for p in patterns if p.get('severity') == 'high')
                medium_risk = sum(1 for p in patterns if p.get('severity') == 'medium')
                low_risk = sum(1 for p in patterns if p.get('severity') == 'low')
                
                # Determine SAR categories
                categories = {}
                
                if high_risk >= 3:
                    categories['Immediate SAR Filing Required'] = high_risk
                    categories['Enhanced Due Diligence'] = medium_risk
                    categories['Monitoring'] = low_risk
                elif high_risk >= 1:
                    categories['SAR Filing Recommended'] = high_risk
                    categories['Further Review Required'] = medium_risk
                    categories['Normal Monitoring'] = low_risk
                elif medium_risk >= 3:
                    categories['Enhanced Review Required'] = medium_risk
                    categories['Standard Monitoring'] = low_risk
                else:
                    categories['Standard Monitoring'] = medium_risk + low_risk
                    if high_risk == 0 and medium_risk == 0:
                        categories['Low Risk'] = 1
                
                labels = list(categories.keys())
                sizes = list(categories.values())
                
                # Color scheme based on risk
                color_map = {
                    'Immediate SAR Filing Required': '#c0392b',
                    'SAR Filing Recommended': '#e74c3c',
                    'Enhanced Review Required': '#f39c12',
                    'Enhanced Due Diligence': '#e67e22',
                    'Further Review Required': '#f39c12',
                    'Standard Monitoring': '#3498db',
                    'Normal Monitoring': '#27ae60',
                    'Monitoring': '#2ecc71',
                    'Low Risk': '#27ae60'
                }
                colors_list = [color_map.get(label, '#95a5a6') for label in labels]
            
            # Create pie chart
            fig, ax = plt.subplots(figsize=(10, 8))
            
            wedges, texts, autotexts = ax.pie(
                sizes,
                labels=labels,
                autopct='%1.1f%%',
                startangle=90,
                colors=colors_list,
                textprops={'fontsize': 10, 'weight': 'bold'}
            )
            
            # Make percentage text more visible
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontsize(12)
                autotext.set_weight('bold')
            
            ax.set_title('SAR Filing Recommendation Breakdown', 
                        fontsize=16, weight='bold', pad=20)
            
            # Add total count
            total_patterns = len(patterns)
            fig.text(0.5, 0.02, f'Total Patterns Analyzed: {total_patterns}',
                    ha='center', fontsize=11, style='italic')
            
            plt.tight_layout()
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            return str(output_path)
        
        except Exception as e:
            logger.error(f"Error creating SAR pie chart: {e}")
            plt.close()
            return None
    
    def _create_spider_chart(
        self,
        patterns: List[Dict[str, Any]],
        output_path: Path
    ) -> Optional[str]:
        """Create spider/radar chart for highest risk account showing pattern distribution."""
        try:
            if not patterns:
                return None
            
            # Find the highest risk account
            account_patterns = {}  # account_id -> {pattern_type: count}
            account_severity = {}  # account_id -> total severity score
            
            for pattern in patterns:
                severity_score = {"high": 3, "medium": 2, "low": 1}.get(pattern.get("severity", "low"), 0)
                pattern_type = pattern.get('pattern_type', 'unknown')
                
                for account in pattern.get('accounts_involved', []):
                    if account not in account_patterns:
                        account_patterns[account] = {}
                        account_severity[account] = 0
                    
                    account_patterns[account][pattern_type] = account_patterns[account].get(pattern_type, 0) + 1
                    account_severity[account] += severity_score
            
            if not account_severity:
                return None
            
            # Get highest risk account
            highest_risk_account = max(account_severity.items(), key=lambda x: x[1])[0]
            account_data = account_patterns[highest_risk_account]
            
            # Get all unique pattern types across all patterns
            all_pattern_types = list(set(p.get('pattern_type', 'unknown') for p in patterns))
            
            # If only one pattern type, can't make a spider chart
            if len(all_pattern_types) < 3:
                return None
            
            # Prepare data for spider chart
            categories = [ptype.replace('_', ' ').title() for ptype in all_pattern_types]
            values = [account_data.get(ptype, 0) for ptype in all_pattern_types]
            
            # Create spider chart
            fig = plt.figure(figsize=(10, 10))
            ax = fig.add_subplot(111, projection='polar')
            
            # Number of variables
            num_vars = len(categories)
            
            # Compute angle for each axis
            angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
            
            # Complete the loop
            values += values[:1]
            angles += angles[:1]
            
            # Plot
            ax.plot(angles, values, 'o-', linewidth=2, color='#e74c3c', label=f'Account: {highest_risk_account[:20]}')
            ax.fill(angles, values, alpha=0.25, color='#e74c3c')
            
            # Fix axis to go in the right order
            ax.set_theta_offset(np.pi / 2)
            ax.set_theta_direction(-1)
            
            # Draw axis lines for each angle and label
            ax.set_xticks(angles[:-1])
            ax.set_xticklabels(categories, size=10, weight='bold')
            
            # Set y-axis limits
            max_value = max(values) if max(values) > 0 else 1
            ax.set_ylim(0, max_value + 1)
            
            # Add gridlines
            ax.grid(True, linestyle='--', alpha=0.7)
            
            # Title and legend
            account_display = highest_risk_account[:30] + "..." if len(highest_risk_account) > 30 else highest_risk_account
            plt.title(f'Highest Risk Account: {account_display}\nAML Pattern Distribution', 
                     size=14, weight='bold', pad=20)
            
            # Add legend with total risk score
            total_score = account_severity[highest_risk_account]
            plt.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1), 
                      title=f'Total Risk Score: {total_score}', fontsize=10)
            
            # Add value labels on each point
            for angle, value, category in zip(angles[:-1], values[:-1], categories):
                if value > 0:
                    ax.text(angle, value + 0.2, str(int(value)), 
                           ha='center', va='center', fontsize=10, 
                           weight='bold', color='#c0392b')
            
            # Add explanation text
            fig.text(0.5, 0.02, 
                    'Each axis represents an AML pattern type. Higher values indicate more patterns detected.',
                    ha='center', fontsize=9, style='italic')
            
            plt.tight_layout()
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            return str(output_path)
        
        except Exception as e:
            logger.error(f"Error creating spider chart: {e}")
            import traceback
            traceback.print_exc()
            plt.close()
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

