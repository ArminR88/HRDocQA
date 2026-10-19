from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
import json
import os

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "HR_dummy_docs")
os.makedirs(OUTPUT_DIR, exist_ok=True)

styles = getSampleStyleSheet()
title_style = ParagraphStyle("Title", parent=styles["Heading1"], fontSize=18, spaceAfter=20)
body_style = styles["BodyText"]

documents = {
    "employee_handbook.pdf": [
        ("Employee Handbook", [
            "Welcome to Acme Corp. This handbook outlines the policies, procedures, and expectations for all employees.",
            "Working Hours: Standard working hours are 9:00 AM to 5:00 PM, Monday through Friday. Flexible arrangements may be approved by your manager.",
            "Code of Conduct: Employees are expected to act professionally, treat colleagues with respect, and avoid conflicts of interest.",
            "Dress Code: Business casual attire is expected in the office. Casual dress is permitted on Fridays.",
            "Remote Work: Employees may work remotely up to two days per week with manager approval.",
        ]),
    ],
    "leave_policy.pdf": [
        ("Leave and Time-Off Policy", [
            "Annual Leave: Full-time employees accrue 20 days of paid annual leave per year, accruing 1.67 days per month.",
            "Sick Leave: Employees receive 10 paid sick days per year. A doctor's note is required for absences exceeding three consecutive days.",
            "Parental Leave: Primary caregivers are entitled to 16 weeks of paid parental leave. Secondary caregivers receive 6 weeks.",
            "Bereavement Leave: Employees may take up to 5 paid days for the death of an immediate family member.",
            "Unpaid Leave: Requests for unpaid leave must be submitted to HR at least 30 days in advance.",
        ]),
    ],
    "performance_review.pdf": [
        ("Performance Review Procedure", [
            "Review Cycle: Performance reviews are conducted twice per year, in June and December.",
            "Rating Scale: Employees are rated on a 5-point scale from 'Does Not Meet Expectations' to 'Outstanding'.",
            "Self-Assessment: Employees must complete a self-assessment form two weeks before the review meeting.",
            "Goal Setting: SMART goals are set at the beginning of each review cycle and tracked quarterly.",
            "Promotion Criteria: Promotions require sustained 'Exceeds Expectations' ratings for at least two consecutive cycles.",
        ]),
    ],
    "benefits_guide.pdf": [
        ("Employee Benefits Guide", [
            "Health Insurance: Acme Corp offers comprehensive medical, dental, and vision coverage. Enrollment is during the first 30 days of employment.",
            "Retirement Plan: The company matches 401(k) contributions up to 5% of salary after one year of service.",
            "Wellness Program: Employees receive a $500 annual wellness stipend for gym memberships or fitness equipment.",
            "Life Insurance: Company-paid life insurance equal to 2x annual salary is provided to all full-time employees.",
            "Employee Assistance Program: Free confidential counseling is available 24/7 through our EAP partner.",
        ]),
    ],
    "workplace_conduct.pdf": [
        ("Workplace Conduct and Anti-Harassment Policy", [
            "Zero Tolerance: Acme Corp has zero tolerance for harassment, discrimination, or retaliation of any kind.",
            "Reporting: Concerns should be reported to your manager, HR, or via the anonymous ethics hotline.",
            "Investigation: All reports are investigated promptly and confidentially. Retaliation against reporters is prohibited.",
            "Social Media: Employees must not post confidential company information or disparage colleagues online.",
            "Conflict of Interest: Employees must disclose any outside employment or financial interests that may conflict with their role.",
        ]),
    ],
    "recruitment_policy.pdf": [
        ("Recruitment and Hiring Policy", [
            "Equal Opportunity: Acme Corp is an equal opportunity employer and does not discriminate based on race, gender, age, religion, or disability.",
            "Job Postings: All open positions must be posted internally for at least 5 business days before external advertising.",
            "Interview Process: A minimum of two structured interviews are required for all positions.",
            "Background Checks: Employment offers are contingent on successful completion of a background check.",
            "Referral Bonus: Employees who refer a successful hire receive $2,000 after the new hire completes 90 days.",
        ]),
    ],
    "onboarding_checklist.pdf": [
        ("New Employee Onboarding Checklist", [
            "Day 1: Complete HR paperwork, receive equipment, and attend orientation.",
            "Week 1: Meet your team, complete mandatory compliance training, and set up accounts.",
            "Week 2-4: Shadow a senior colleague and complete role-specific training.",
            "Day 30: Check-in meeting with your manager to review progress.",
            "Day 90: Formal probation review and goal-setting session.",
        ]),
    ],
    "training_development.pdf": [
        ("Training and Development Policy", [
            "Learning Budget: Each employee receives $1,500 per year for professional development courses and conferences.",
            "Mandatory Training: All employees must complete annual compliance and security awareness training.",
            "Tuition Reimbursement: Up to $5,000 per year is available for job-related degree programs, subject to manager approval.",
            "Certifications: The company reimburses exam fees for approved professional certifications upon successful completion.",
            "Internal Mobility: Employees with 12+ months of tenure may apply for internal transfers.",
        ]),
    ],
    "compensation_policy.pdf": [
        ("Compensation and Salary Structure", [
            "Pay Philosophy: Acme Corp benchmarks salaries against market data annually to ensure competitive pay.",
            "Pay Bands: Each role is assigned to a pay band with a defined minimum, midpoint, and maximum salary.",
            "Annual Review: Salaries are reviewed annually in January based on performance and market adjustments.",
            "Bonuses: Discretionary annual bonuses are based on individual and company performance.",
            "Overtime: Non-exempt employees are paid 1.5x their regular rate for hours worked beyond 40 per week.",
        ]),
    ],
    "expense_reimbursement.pdf": [
        ("Expense Reimbursement Policy", [
            "Submission: Expense reports must be submitted within 30 days of the expense date with original receipts.",
            "Approval: All expenses over $500 require manager approval; expenses over $2,000 require director approval.",
            "Travel: Economy class is standard for flights under 6 hours; business class is permitted for longer flights.",
            "Meals: Daily meal allowance is $75 for domestic travel and $100 for international travel.",
            "Corporate Card: Employees traveling more than 4 times per year are issued a corporate credit card.",
        ]),
    ],
    "travel_policy.pdf": [
        ("Business Travel Policy", [
            "Booking: All business travel must be booked through the company's approved travel portal.",
            "Accommodation: Standard hotel rate is capped at $250 per night in major cities.",
            "Ground Transport: Ride-sharing and rental cars are reimbursable; rental cars require manager approval.",
            "Advance Approval: All international travel requires VP approval at least 14 days in advance.",
            "Travel Insurance: Company-provided travel insurance covers all business trips.",
        ]),
    ],
    "it_security.pdf": [
        ("IT Security and Acceptable Use Policy", [
            "Passwords: Passwords must be at least 12 characters and rotated every 90 days.",
            "Multi-Factor Authentication: MFA is mandatory for all company systems.",
            "Device Usage: Company devices are for business use; limited personal use is permitted.",
            "Data Handling: Confidential data must not be stored on personal devices or unapproved cloud services.",
            "Incident Reporting: Suspected security incidents must be reported to IT within 1 hour.",
        ]),
    ],
    "health_safety.pdf": [
        ("Health and Safety Policy", [
            "Workplace Safety: Acme Corp is committed to providing a safe work environment for all employees.",
            "Emergency Procedures: Fire drills are conducted quarterly; evacuation routes are posted on each floor.",
            "First Aid: Trained first-aiders are available on each floor; first aid kits are located in every kitchen.",
            "Reporting Hazards: Employees must report hazards or unsafe conditions to Facilities immediately.",
            "Ergonomics: Employees may request ergonomic assessments and equipment through HR.",
        ]),
    ],
    "disciplinary_procedure.pdf": [
        ("Disciplinary Procedure", [
            "Purpose: This procedure ensures fair and consistent handling of performance or conduct issues.",
            "Verbal Warning: First-level issues are addressed through a documented verbal warning.",
            "Written Warning: Repeated or more serious issues result in a formal written warning.",
            "Final Warning: Serious misconduct may result in a final written warning.",
            "Termination: Gross misconduct or repeated violations may result in termination of employment.",
        ]),
    ],
    "grievance_policy.pdf": [
        ("Grievance Policy", [
            "Right to Raise: All employees have the right to raise grievances without fear of retaliation.",
            "Informal Resolution: Employees are encouraged to first raise concerns directly with their manager.",
            "Formal Grievance: Formal grievances must be submitted in writing to HR within 30 days of the incident.",
            "Investigation: HR will investigate and respond within 10 business days.",
            "Appeal: Employees may appeal the outcome to the HR Director within 5 business days.",
        ]),
    ],
    "diversity_inclusion.pdf": [
        ("Diversity and Inclusion Policy", [
            "Commitment: Acme Corp is committed to building a diverse and inclusive workforce.",
            "Recruitment: Hiring practices are designed to reduce unconscious bias, including diverse interview panels.",
            "Employee Resource Groups: ERGs for women, LGBTQ+, veterans, and underrepresented groups are supported by the company.",
            "Training: All managers complete annual diversity and inclusion training.",
            "Reporting: Discrimination or bias incidents should be reported to HR immediately.",
        ]),
    ],
    "overtime_policy.pdf": [
        ("Overtime Policy", [
            "Eligibility: Non-exempt employees are eligible for overtime pay at 1.5x their regular rate.",
            "Approval: All overtime must be approved in advance by a manager.",
            "Tracking: Employees must record all hours worked accurately in the time-tracking system.",
            "Maximum Hours: Employees should not exceed 60 hours of work per week without HR approval.",
            "Compensatory Time: Exempt employees may receive comp time for weekend or holiday work at manager discretion.",
        ]),
    ],
    "termination_offboarding.pdf": [
        ("Termination and Offboarding Procedure", [
            "Resignation: Employees should provide at least 2 weeks' written notice of resignation.",
            "Exit Interview: HR conducts exit interviews to gather feedback from departing employees.",
            "Equipment Return: All company equipment must be returned on the last day of employment.",
            "Final Pay: Final paychecks are issued on the next regular payday after termination.",
            "COBRA: Departing employees receive information about COBRA health insurance continuation.",
        ]),
    ],
    "referral_program.pdf": [
        ("Employee Referral Program", [
            "Eligibility: All employees except HR staff and hiring managers may participate.",
            "Bonus: A $2,000 bonus is paid after the referred employee completes 90 days of employment.",
            "Exclusions: Referrals of former employees who left within the past 12 months are not eligible.",
            "Submission: Referrals must be submitted through the company careers portal.",
            "Payment: Bonuses are paid in the payroll cycle following the 90-day mark.",
        ]),
    ],
    "flexible_working.pdf": [
        ("Flexible Working Policy", [
            "Eligibility: All employees who have completed 6 months of service may request flexible working.",
            "Types: Options include remote work, compressed hours, flexitime, and part-time arrangements.",
            "Request Process: Requests must be submitted in writing to your manager 30 days in advance.",
            "Trial Period: Approved arrangements are trialed for 3 months before becoming permanent.",
            "Review: Flexible arrangements are reviewed annually as part of performance discussions.",
        ]),
    ],
    "drug_alcohol.pdf": [
        ("Drug and Alcohol Policy", [
            "Zero Tolerance: Acme Corp prohibits the use, possession, or distribution of illegal drugs on company premises.",
            "Alcohol: Alcohol may only be consumed at company-sponsored events with manager approval.",
            "Fitness for Duty: Employees must report to work free from the influence of drugs or alcohol.",
            "Testing: Drug and alcohol testing may be required for safety-sensitive roles or after workplace incidents.",
            "Support: Employees struggling with substance abuse are encouraged to contact the EAP for confidential help.",
        ]),
    ],
    "data_privacy.pdf": [
        ("Data Privacy and Protection Policy", [
            "Scope: This policy covers all personal and business data collected, stored, or processed by Acme Corp.",
            "GDPR Compliance: Acme Corp complies with GDPR and other applicable data protection laws.",
            "Data Access: Employees may only access data necessary for their role.",
            "Data Breach: Suspected data breaches must be reported to the Data Protection Officer within 24 hours.",
            "Retention: Personal data is retained only as long as necessary for business or legal purposes.",
        ]),
    ],
    "exit_interview.pdf": [
        ("Exit Interview Guidelines", [
            "Purpose: Exit interviews gather feedback to improve employee experience and retention.",
            "Timing: Exit interviews are scheduled during the final week of employment.",
            "Format: Interviews may be conducted in person or via video call, lasting 30-45 minutes.",
            "Confidentiality: Feedback is aggregated and anonymized before being shared with leadership.",
            "Optional: Employees may decline an exit interview without any impact on their final pay or references.",
        ]),
    ],
    "relocation_policy.pdf": [
        ("Employee Relocation Policy", [
            "Eligibility: Relocation assistance is offered to employees transferring to a new location at company request.",
            "Lump Sum: A lump sum of up to $10,000 is provided to cover moving costs.",
            "Temporary Housing: Up to 60 days of temporary housing is provided for relocating employees.",
            "House Hunting: One paid house-hunting trip is provided for the employee and one partner.",
            "Repayment: Relocation benefits must be repaid if the employee leaves within 12 months.",
        ]),
    ],
    "whistleblower_policy.pdf": [
        ("Whistleblower Policy", [
            "Protection: Acme Corp prohibits retaliation against employees who report concerns in good faith.",
            "Scope: Reports may cover financial fraud, safety violations, harassment, or other misconduct.",
            "Reporting Channels: Concerns may be reported to HR, Legal, or the anonymous ethics hotline.",
            "Investigation: All reports are investigated promptly and confidentially.",
            "Confidentiality: The identity of the reporter is protected to the extent permitted by law.",
        ]),
    ],
}

# --- Generate PDFs into HR_dummy_docs ---
for filename, entries in documents.items():
    filepath = os.path.join(OUTPUT_DIR, filename)
    doc = SimpleDocTemplate(filepath, pagesize=letter)
    story = []
    for index, (title, paragraphs) in enumerate(entries):
        if index > 0:
            story.append(Spacer(1, 24))
        story.append(Paragraph(title, title_style))
        for p in paragraphs:
            story.append(Paragraph(p, body_style))
            story.append(Spacer(1, 12))
    doc.build(story)
    print(f"Created {filepath}")

# --- Generate Evaluation Q&A file into HR_dummy_docs ---
qa_pairs = [
    {"question": "How many days of annual leave do full-time employees get?", "answer": "20 days per year, accruing 1.67 days per month.", "source": "leave_policy.pdf"},
    {"question": "What is the 401(k) match?", "answer": "The company matches up to 5% of salary after one year of service.", "source": "benefits_guide.pdf"},
    {"question": "How many weeks of parental leave do primary caregivers get?", "answer": "16 weeks of paid parental leave.", "source": "leave_policy.pdf"},
    {"question": "What is the employee referral bonus?", "answer": "$2,000, paid after the referred employee completes 90 days.", "source": "referral_program.pdf"},
    {"question": "How often are performance reviews conducted?", "answer": "Twice per year, in June and December.", "source": "performance_review.pdf"},
    {"question": "What is the annual learning budget per employee?", "answer": "$1,500 per year for professional development.", "source": "training_development.pdf"},
    {"question": "How many days a week can employees work remotely?", "answer": "Up to two days per week with manager approval.", "source": "employee_handbook.pdf"},
    {"question": "What is the daily meal allowance for international travel?", "answer": "$100 per day for international travel.", "source": "expense_reimbursement.pdf"},
    {"question": "How long must passwords be and how often rotated?", "answer": "At least 12 characters, rotated every 90 days.", "source": "it_security.pdf"},
    {"question": "How much is the annual wellness stipend?", "answer": "$500 per year for gym memberships or fitness equipment.", "source": "benefits_guide.pdf"},
    {"question": "How many days of written notice are required for resignation?", "answer": "At least 2 weeks' written notice.", "source": "termination_offboarding.pdf"},
    {"question": "What is the maximum hotel rate for business travel in major cities?", "answer": "$250 per night in major cities.", "source": "travel_policy.pdf"},
    {"question": "How many weeks of paid parental leave do secondary caregivers get?", "answer": "6 weeks.", "source": "leave_policy.pdf"},
    {"question": "When must a suspected data breach be reported?", "answer": "Within 24 hours to the Data Protection Officer.", "source": "data_privacy.pdf"},
    {"question": "What is the relocation lump sum amount?", "answer": "Up to $10,000 to cover moving costs.", "source": "relocation_policy.pdf"},
]

qa_path = os.path.join(OUTPUT_DIR, "eval_qa_pairs.json")
with open(qa_path, "w") as f:
    json.dump(qa_pairs, f, indent=2)
print(f"Created {qa_path}")

print(f"\nDone! Generated {len(documents)} PDFs + 1 Q&A file in '{OUTPUT_DIR}/'")