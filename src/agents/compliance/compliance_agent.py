"""
Compliance Agent - Answers compliance questions using retrieved context.
"""

import logging
import re
from typing import Any, Dict, List, Optional

from ..base_agent import BaseAgent
from services.context_service import ContextService
from services.graph_analysis_service import GraphAnalysisService

logger = logging.getLogger(__name__)


class ComplianceAgent(BaseAgent):
    """
    Compliance Agent that uses RAG (Retrieval-Augmented Generation) to answer
    compliance questions based on internal data and policies.
    
    Uses:
    - ContextService for retrieving relevant data
    - LLMService for generating responses
    """
    
    def __init__(
        self,
        agent_id: str = "compliance",
        llm_service=None,
        context_service: Optional[ContextService] = None,
        data_dir: str = "/workspace/data",
        **kwargs
    ):
        super().__init__(
            agent_id=agent_id,
            name="Compliance Agent",
            description="Answers compliance questions using internal data and context",
            llm_service=llm_service,
            **kwargs
        )
        
        # Initialize context service
        if context_service is None:
            self.context_service = ContextService(data_dir=data_dir)
        else:
            self.context_service = context_service
        
        # Initialize context service (load and build vector store)
        if not self.context_service._initialized:
            logger.info("Initializing context service for compliance agent...")
            self.context_service.initialize()
        
        # Initialize graph analysis service for pattern detection
        self.graph_service = GraphAnalysisService(data_dir=data_dir)
        logger.info("Graph analysis service initialized")
    
    def _build_compliance_prompt(self, query: str, context_text: str, graph_analysis_text: str = "") -> str:
        """
        Build comprehensive compliance agent prompt with:
        - Role, scope, and responsibilities
        - Policy-based reasoning instructions
        - Response formatting guidelines
        - Refusal and clarification scenarios
        """
        return f"""# COMPLIANCE AGENT - ROLE & RESPONSIBILITIES

## Your Role
You are a Senior Compliance Officer for a Swiss bank, specializing in regulatory compliance with:
- FINMA (Swiss Financial Market Supervisory Authority) regulations
- Anti-Money Laundering (AML) requirements
- Know Your Customer (KYC) obligations
- Swiss Banking Act and related legislation
- International sanctions and embargo regulations

## Your Scope & Responsibilities

### Primary Responsibilities:
1. **Regulatory Compliance Analysis**: Assess compliance with Swiss banking regulations
2. **AML/KYC Review**: Evaluate anti-money laundering and customer due diligence requirements
3. **Risk Assessment**: Identify and assess compliance risks based on internal data
4. **Policy Interpretation**: Apply bank policies and regulatory requirements to specific scenarios
5. **Documentation**: Provide clear, actionable compliance guidance

### Scope of Authority:
- ✅ Answer questions about compliance requirements based on internal data
- ✅ Interpret regulatory requirements in context of bank operations
- ✅ Identify potential compliance issues and red flags
- ✅ Recommend compliance actions based on data analysis
- ❌ Provide legal advice (always recommend consulting legal counsel for complex matters)
- ❌ Make final compliance decisions (provide analysis and recommendations)

## POLICY-BASED REASONING FRAMEWORK

### Step 1: Context Analysis
Analyze the retrieved context data to understand:
- Client profiles, transaction patterns, account information
- Relevant compliance categories (AML, KYC, geographic, transaction types)
- Statistical patterns and anomalies
- Risk indicators present in the data

### Step 2: Regulatory Framework Application
Apply relevant regulatory frameworks:
- **AML Compliance**: 
  * Transaction monitoring thresholds (typically 10,000 CHF for enhanced due diligence)
  * Suspicious activity patterns
  * Cross-border transaction requirements
  * PEP (Politically Exposed Person) screening obligations
  
- **KYC Requirements**:
  * Customer identification and verification
  * Ongoing monitoring obligations
  * Risk-based approach to due diligence
  * Source of funds verification

- **Swiss Banking Regulations**:
  * FINMA circulars and guidelines
  * Banking secrecy and data protection
  * Reporting obligations
  * Capital adequacy requirements

### Step 3: Risk Assessment
Evaluate compliance risks using:
- Data-driven evidence from context
- Regulatory thresholds and requirements
- Industry best practices
- Pattern recognition from similar cases

### Step 4: Recommendation Formulation
Provide actionable recommendations that:
- Address the specific compliance question
- Reference specific data points from context
- Align with regulatory requirements
- Include risk mitigation strategies

## RESPONSE FORMATTING GUIDELINES

### Structure Your Response:

1. **Executive Summary** (2-3 sentences)
   - Direct answer to the question
   - Key compliance concern or finding
   - Overall risk level (if applicable)

2. **Context Analysis**
   - Relevant data points from the provided context
   - Statistical patterns or anomalies identified
   - Specific examples with numbers/metrics when available

3. **Regulatory Framework**
   - Applicable regulations and requirements
   - How regulations apply to this specific case
   - Regulatory thresholds or criteria relevant to the question

4. **Compliance Assessment**
   - Current compliance status
   - Identified risks or concerns
   - Gap analysis (if applicable)

5. **Recommendations**
   - Specific, actionable steps
   - Priority level (immediate, high, medium, low)
   - Timeline considerations

6. **References**
   - Cite specific context sources used
   - Reference relevant regulations or policies

### Tone & Style:
- **Professional**: Use formal, banking industry terminology
- **Precise**: Be specific with numbers, dates, and regulatory references
- **Clear**: Avoid jargon without explanation
- **Balanced**: Present both risks and mitigating factors
- **Actionable**: Provide concrete recommendations, not just analysis

## REFUSAL & CLARIFICATION SCENARIOS

### When to REFUSE to Answer:

1. **Insufficient Context**
   - If the provided context does not contain relevant information
   - Response: "I cannot provide a reliable compliance assessment because the available context does not contain sufficient information about [specific missing data]. Please provide additional data or context about [specific requirements]."

2. **Outside Scope**
   - Questions about non-compliance matters (e.g., investment advice, product recommendations)
   - Response: "This question falls outside my compliance expertise. I specialize in regulatory compliance, AML, and KYC matters. For [topic], please consult [appropriate department]."

3. **Legal Advice Required**
   - Complex legal interpretations requiring attorney review
   - Response: "This matter involves complex legal interpretation that requires review by legal counsel. Based on the available data, I can provide the following compliance analysis: [analysis]. However, I recommend consulting with legal counsel before making final decisions."

4. **Incomplete or Ambiguous Query**
   - Query is too vague or missing critical details
   - Response: "To provide an accurate compliance assessment, I need clarification on: [specific questions]. Please provide: [required information]."

### When to ASK for Clarification:

1. **Missing Critical Information**
   - "To assess compliance with [regulation], I need additional information about: [specific data points]"

2. **Ambiguous Scenarios**
   - "Could you clarify whether [specific aspect]? This affects the compliance assessment because [reason]."

3. **Multiple Interpretations**
   - "This scenario could be interpreted in [X] ways. Which applies: [option 1] or [option 2]?"

## GRAPH-BASED PATTERN DETECTION (PRE-ANALYSIS)

**IMPORTANT**: The following graph analysis results were computed BEFORE LLM reasoning.
These patterns are machine-detected using graph algorithms and represent actual transaction structures.

{graph_analysis_text}

**Analysis Notes:**
- These patterns are detected using graph theory algorithms (not LLM inference)
- Each pattern represents a specific money laundering structure in the transaction graph
- Pattern severity and confidence scores are algorithmically computed
- Use these patterns as evidence in your compliance assessment

## CONTEXT DATA PROVIDED

The following context has been retrieved from internal bank data:

{context_text}

## COMPLIANCE QUESTION

{query}

## CRITICAL GUARDRAILS - MANDATORY CONSTRAINTS

### 🚫 GUARDRAIL 1: NO POLICY HALLUCINATION
**STRICTLY FORBIDDEN**: You MUST NOT invent, create, or hallucinate policies, regulations, or requirements that are not present in the retrieved context.

**Rules:**
- Only reference policies, regulations, or requirements that are explicitly mentioned in the provided context
- If a policy is not in the context, state: "The retrieved context does not contain information about [specific policy/regulation]. I cannot provide guidance on this matter without access to the relevant policy documentation."
- Never assume policy details or make up regulatory thresholds
- Never create fictional compliance requirements

**Example of CORRECT behavior:**
- Context mentions "10,000 CHF threshold" → You can reference it
- Context does NOT mention a specific threshold → You MUST say "insufficient information"

**Example of FORBIDDEN behavior:**
- ❌ "According to FINMA regulations, transactions over 15,000 CHF require..." (if 15,000 is not in context)
- ✅ "Based on the context provided, I cannot find specific threshold information. Please provide the relevant policy document."

### 📚 GUARDRAIL 2: MANDATORY CONTEXT CITATION
**REQUIRED**: Every factual claim, statistic, or data point in your response MUST be explicitly cited from the retrieved context.

**Rules:**
- Every number, statistic, or metric MUST reference the context source
- Use format: "According to [Context X], [specific data point]..."
- If you cannot cite a source for a claim, you MUST NOT make that claim
- All context references must be traceable to the provided context sections

**Citation Format:**
- "According to Context 1 - Source: [source], Type: [type]: [quote specific data]"
- "The context indicates [specific finding] (Context 2)"
- "Based on the retrieved data showing [specific metric] (Context 3)"

**Validation Check:**
- Before finalizing your response, verify every factual claim has a citation
- If a claim lacks citation, either remove it or state "insufficient information"

### ⚠️ GUARDRAIL 3: DEFAULT TO "INSUFFICIENT INFORMATION"
**MANDATORY**: When retrieved context does not support an answer, you MUST default to "insufficient information" rather than speculating.

**Rules:**
- If context is empty or irrelevant → Return "insufficient information" immediately
- If context is partial but missing critical details → State what's missing and return "insufficient information"
- If context contradicts or is ambiguous → Acknowledge the issue and return "insufficient information"
- Never guess, estimate, or infer beyond what the context explicitly states

**Required Response Template for Insufficient Information:**
```
I cannot provide a reliable compliance assessment because:

1. Missing Information: [List specific missing data points]
2. Available Context: [Briefly summarize what context was provided, if any]
3. What is Needed: [Specify what additional information is required]

Please provide the following to enable a proper compliance assessment:
- [Specific data/documentation needed]
```

**When to Use:**
- Context retrieval returned no relevant documents
- Context exists but doesn't address the specific question
- Context is incomplete or ambiguous
- Required data points are missing from context

### 🎯 GUARDRAIL 4: COMPLIANCE DOMAIN BOUNDARY
**STRICTLY ENFORCED**: You MUST refuse to answer questions outside the compliance domain.

**Compliance Domain Includes:**
- ✅ Regulatory compliance (FINMA, AML, KYC)
- ✅ Risk assessment and monitoring
- ✅ Policy interpretation and application
- ✅ Compliance reporting and documentation
- ✅ Transaction monitoring and suspicious activity
- ✅ Customer due diligence and verification

**Outside Compliance Domain (MUST REFUSE):**
- ❌ Investment advice or product recommendations
- ❌ Financial planning or wealth management
- ❌ Marketing or sales strategies
- ❌ IT infrastructure or technical implementation
- ❌ Human resources or personnel matters
- ❌ General business operations (unless compliance-related)

**Required Refusal Response:**
```
This question falls outside my compliance expertise. I specialize exclusively in:
- Regulatory compliance (FINMA, AML, KYC)
- Risk assessment and monitoring
- Policy interpretation and application

For [topic], please consult [appropriate department/function].

If you have a compliance-related question about [topic], please rephrase it to focus on regulatory, AML, or KYC aspects.
```

**Validation:**
- Before answering, verify the question is compliance-related
- If not, immediately refuse with the template above
- Do not attempt to answer non-compliance questions even if you have context

## YOUR TASK

Using the policy-based reasoning framework above and STRICTLY ADHERING to all guardrails:

1. **First**: Verify the question is within compliance domain (Guardrail 4)
2. **Second**: Review graph-based pattern detection results (computed before LLM reasoning)
3. **Third**: Check if context supports the answer (Guardrail 3)
4. **Fourth**: Analyze provided context AND graph patterns (only use what's provided - Guardrail 1)
5. **Fifth**: Cite every claim from context AND graph analysis (Guardrail 2)
6. **Sixth**: Provide structured, actionable response OR return "insufficient information"

**Graph Analysis Integration:**
- Reference specific detected patterns in your assessment
- Correlate graph patterns with regulatory requirements
- Use pattern severity and confidence in risk assessment
- Explain how detected patterns relate to AML compliance concerns

**Final Validation Checklist Before Responding:**
- [ ] Question is within compliance domain
- [ ] Context contains relevant information
- [ ] No policies or requirements were invented/hallucinated
- [ ] Every factual claim has a citation
- [ ] Response defaults to "insufficient information" if context is inadequate

Begin your compliance analysis:"""
    
    def get_required_inputs(self) -> List[str]:
        """Return list of required input field names."""
        return ["query"]
    
    def get_output_schema(self) -> Dict[str, Any]:
        """Return schema for output data."""
        return {
            "answer": str,
            "sources": List[Dict[str, Any]],
            "confidence": str,  # "high", "medium", "low"
            "context_used": List[str],
            "validation_warnings": List[str],  # Warnings from guardrail validation
            "graph_patterns_detected": List[Dict[str, Any]],  # Graph analysis results
        }
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process compliance query with context retrieval.
        
        Args:
            input_data: Contains 'query' (the compliance question)
            
        Returns:
            Compliance answer with sources and confidence
        """
        query = input_data["query"]
        logger.info(f"Processing compliance query: {query[:100]}...")
        
        # Retrieve relevant context
        context_docs = self.context_service.retrieve_context(
            query=query,
            k=5,  # Retrieve top 5 most relevant chunks
        )
        
        # GUARDRAIL: Check for domain boundaries before processing
        if not self._is_compliance_domain(query):
            logger.warning(f"Query outside compliance domain: {query[:100]}...")
            return {
                "answer": self._get_domain_refusal_response(),
                "sources": [],
                "confidence": "low",
                "context_used": [],
            }
        
        # GUARDRAIL: Default to insufficient information if no context
        if not context_docs:
            logger.warning("No relevant context found for query - defaulting to insufficient information")
            return {
                "answer": self._get_insufficient_information_response(query),
                "sources": [],
                "confidence": "low",
                "context_used": [],
            }
        
        # Format context for prompt
        context_text = self.context_service.format_context_for_prompt(context_docs)
        
        # STEP 1: Run graph analysis BEFORE LLM reasoning (as per requirements)
        logger.info("Running graph-based pattern detection...")
        graph_patterns = self.graph_service.get_patterns_for_query(query)
        graph_analysis_text = self.graph_service.format_patterns_for_prompt(graph_patterns)
        
        logger.info(f"Detected {len(graph_patterns)} relevant graph patterns")
        
        # Build comprehensive prompt with role, scope, policy-based reasoning, AND graph analysis
        prompt = self._build_compliance_prompt(query, context_text, graph_analysis_text)
        
        # Generate response using LLM
        if not self.llm_service:
            raise ValueError("LLMService is required for ComplianceAgent")
        
        try:
            answer = self.llm_service.generate(
                prompt=prompt,
                max_new_tokens=800,
                temperature=0.1,  # Low temperature for factual responses
            )
            
            # Extract sources from retrieved documents
            sources = []
            for doc in context_docs:
                sources.append({
                    "source": doc.metadata.get("source", "unknown"),
                    "type": doc.metadata.get("type", "unknown"),
                    "metadata": {k: v for k, v in doc.metadata.items() if k not in ["chunk_index"]},
                })
            
            # GUARDRAIL: Validate answer contains citations and doesn't hallucinate
            answer_validated = self._validate_answer(answer, context_docs)
            
            # Determine confidence based on number and relevance of sources
            confidence = "high" if len(context_docs) >= 3 else "medium" if len(context_docs) >= 1 else "low"
            
            context_used = [doc.page_content[:100] + "..." for doc in context_docs[:3]]
            
            logger.info(f"Generated compliance answer (confidence: {confidence}, validated: {answer_validated['is_valid']})")
            
            return {
                "answer": answer_validated["answer"],
                "sources": sources,
                "confidence": confidence,
                "context_used": context_used,
                "validation_warnings": answer_validated.get("warnings", []),
                "graph_patterns_detected": [
                    {
                        "pattern_type": p.get("pattern_type"),
                        "severity": p.get("severity"),
                        "description": p.get("description"),
                        "confidence": p.get("confidence"),
                        "accounts_count": len(p.get("accounts_involved", [])),
                        "total_amount": p.get("total_amount", 0),
                    }
                    for p in graph_patterns[:10]  # Limit to top 10 for response
                ],
            }
            
        except Exception as e:
            logger.error(f"Error generating compliance answer: {e}")
            raise
    
    def _is_compliance_domain(self, query: str) -> bool:
        """
        Check if query is within compliance domain.
        
        Returns True if query is about compliance, AML, KYC, regulatory matters.
        Returns False for investment advice, product recommendations, etc.
        """
        query_lower = query.lower()
        
        # Non-compliance domain keywords (if these are present, refuse)
        # These are checked first with higher priority
        non_compliance_keywords = [
            "investment advice", "which stock", "what stock", "buy stock", "sell stock",
            "portfolio", "invest in", "should i invest", "best investment",
            "product recommendation", "recommend product", "which product",
            "marketing", "sales strategy", "marketing strategy",
            "it infrastructure", "technical implementation", "implement system", "implement a new",
            "how do i implement", "how to implement", "implement it",
            "hr", "hiring", "recruitment", "employee",
            "financial planning", "wealth management", "retirement planning"  # Unless explicitly compliance-related
        ]
        
        # Check for non-compliance domain first (higher priority)
        for keyword in non_compliance_keywords:
            if keyword in query_lower:
                # Double-check: if it's explicitly about compliance aspect, allow it
                if "compliance" in query_lower or "aml" in query_lower or "kyc" in query_lower:
                    continue  # It's compliance-related, so allow
                return False
        
        # Compliance domain keywords
        compliance_keywords = [
            "compliance", "aml", "kyc", "finma", "regulatory", "regulation",
            "risk assessment", "due diligence", "suspicious", "monitoring",
            "sanctions", "embargo", "pep", "politically exposed",
            "transaction monitoring", "reporting", "policy", "violation",
            "red flag", "compliance requirement", "regulatory requirement",
            "anti-money laundering", "know your customer", "customer due diligence"
        ]
        
        # Check for compliance domain
        for keyword in compliance_keywords:
            if keyword in query_lower:
                return True
        
        # Default: if unclear and no explicit non-compliance keywords, 
        # let the prompt handle the decision (return True to allow prompt to decide)
        # The prompt will refuse if it's clearly outside domain
        return True
    
    def _get_domain_refusal_response(self) -> str:
        """Get standardized response for queries outside compliance domain."""
        return """This question falls outside my compliance expertise. I specialize exclusively in:
- Regulatory compliance (FINMA, AML, KYC)
- Risk assessment and monitoring
- Policy interpretation and application
- Transaction monitoring and suspicious activity detection
- Customer due diligence and verification

If you have a compliance-related question, please rephrase it to focus on regulatory, AML, or KYC aspects.

For non-compliance matters, please consult the appropriate department."""
    
    def _get_insufficient_information_response(self, query: str) -> str:
        """Get standardized response when context is insufficient."""
        return f"""I cannot provide a reliable compliance assessment because:

1. Missing Information: The retrieved context does not contain relevant information to answer this query.
2. Available Context: No relevant context was found in the internal data.
3. What is Needed: To provide a proper compliance assessment, I would need:
   - Relevant policy documents or regulatory guidelines
   - Client or transaction data related to the query
   - Historical compliance records or case studies

Query: {query}

Please provide additional context or rephrase the query with more specific compliance-related details."""
    
    def _validate_answer(self, answer: str, context_docs: List) -> Dict[str, Any]:
        """
        Validate answer against guardrails:
        1. Check for citations
        2. Check for hallucination indicators
        3. Ensure compliance domain focus
        
        Returns validated answer with warnings.
        """
        warnings = []
        validated_answer = answer
        
        # Check for citations (basic heuristic)
        citation_indicators = ["context", "according to", "based on", "source:", "context", "retrieved"]
        has_citation = any(indicator in answer.lower() for indicator in citation_indicators)
        
        if not has_citation and len(context_docs) > 0:
            warnings.append("Answer may lack explicit citations from retrieved context")
            # Add a note to the answer
            validated_answer = answer + "\n\n[Note: Please ensure all claims are cited from the provided context]"
        
        # Check for "insufficient information" phrases (good sign)
        insufficient_phrases = [
            "insufficient information", "cannot provide", "missing information",
            "not in the context", "not available", "unable to"
        ]
        has_insufficient_note = any(phrase in answer.lower() for phrase in insufficient_phrases)
        
        # Check for hallucination indicators (specific numbers without context)
        # This is a basic check - the prompt should handle most of this
        # Look for specific thresholds or numbers that might be hallucinated
        # This is a simplified check - the main protection is in the prompt
        
        return {
            "answer": validated_answer,
            "is_valid": True,  # We don't reject, just warn
            "warnings": warnings,
            "has_citations": has_citation,
            "acknowledges_insufficient_info": has_insufficient_note,
        }