print("\n--- DRY RUN: 50 Test Queries ---")
test_queries = [
    # Food safety & temperature
    "What is the minimum freezer temperature?",
    "How often should refrigeration temperature logs be recorded?",
    "What sanitizer must be used on food prep surfaces?",
    "How often should food prep surfaces be sanitized?",
    "What inventory rotation method must be followed for perishables?",
    "What is the safe holding temperature for hot food?",
    "How long can perishable food sit at room temperature before it must be discarded?",

    # Hygiene & staff conduct
    "What is the handwashing procedure?",
    "What uniform items are mandatory for staff?",
    "How long must handwashing take?",
    "How often must staff wash their hands during a shift?",
    "What personal protective equipment is required in the kitchen?",

    # Staffing & operations
    "How many staff are required per shift?",
    "What is the minimum staffing composition per shift?",
    "How long is the basic operational training program for new employees?",
    "How often are staff performance reviews conducted?",
    "What scoring methodology is used for staff performance reviews?",
    "What are the staff performance review requirements?",
    "What is the onboarding process for new hires?",

    # Compliance & regulatory
    "What are the penalties for FSSAI non-compliance?",
    "Where must the FSSAI license be displayed?",
    "How often must pest control services be scheduled?",
    "Who can be used as vendors for sourcing raw ingredients?",
    "What documentation is required for a food safety audit?",
    "What is the process for renewing an FSSAI license?",

    # Customer service
    "How should customer complaints be escalated?",
    "What are the resolution SLAs for different complaint severity categories?",
    "What is the response time requirement for negative social media reviews?",
    "How quickly must floor spills be cleaned up?",
    "What is the refund policy for dissatisfied customers?",

    # Finance & marketing
    "What is the minimum marketing ROI threshold for campaign renewal?",
    "When must cash drops to the safe be performed?",
    "What is the daily cash reconciliation process?",
    "What discount approval limits apply to store managers?",

    # Equipment & maintenance
    "How often must deep fryer oil be changed?",
    "How often must fire extinguishers be inspected?",
    "Who performs the annual fire extinguisher inspection?",
    "What is the maintenance schedule for kitchen exhaust systems?",
    "How often should refrigeration units be serviced?",

    # Store procedures
    "What are the store closing procedures?",
    "How full can waste bins get before they must be emptied?",
    "What happens to the store key when an employee is terminated?",
    "What does the outlet opening checklist cover?",
    "What is the end-of-day cash-up procedure?",

    # Broader domain queries (test retrieval beyond curated SOPs)
    "What labour laws apply to minimum wages in India?",
    "What are OSHA's requirements for workplace safety?",
    "What does the WHO say about food safety standards?",
    "What does the ILO say about working hours regulations?",
    "What are FAO's guidelines on food storage?",
    "What are the legal requirements for franchise disclosure documents?",
    "What health and safety training is legally required for food handlers?",
]

print(f"Total test queries: {len(test_queries)}\n")

for query in test_queries:
    print(f"\nQuery: {query}")
    docs = vectorstore.similarity_search(query, k=1)
    if docs:
        print(f"Answer (Snippet): {docs[0].page_content}")
        print(f"Source: {docs[0].metadata.get('source', 'Unknown')} | ID: {docs[0].metadata.get('id', 'N/A')}")
    else:
        print("No relevant documents found.")