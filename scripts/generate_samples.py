from docx import Document
from pathlib import Path

base = Path(__file__).resolve().parent.parent / 'samples'
base.mkdir(exist_ok=True)

master = Document()
master.add_heading('Master Answer Key - Chartered Accountancy', level=1)
master.add_paragraph('1. Explain the difference between capital expenditure and revenue expenditure. Provide one example of each.')
master.add_paragraph('Answer: Capital expenditure creates long-term benefits and is capitalized; example: purchase of machinery. Revenue expenditure is for day-to-day operations and is expensed in the current period; example: repair and maintenance.')
master.add_paragraph('2. Describe the key steps in the GST input tax credit claim process for a registered business.')
master.add_paragraph('Answer: The business must possess a valid tax invoice, ensure the goods/services are eligible, file the GST return, match the input credit in the return, and maintain supporting records.')
master.add_paragraph('3. Calculate depreciation for machinery purchased for ₹120,000 on 1 April using the straight-line method at 10% per annum for the first year.')
master.add_paragraph('Answer: Depreciation = ₹120,000 × 10% = ₹12,000 for the first year.')
master.save(base / 'chartered_accountancy_master_key.docx')

rubric = Document()
rubric.add_heading('Evaluation Rubric - Chartered Accountancy Quiz', level=1)
rubric.add_paragraph('Total marks: 25')
rubric.add_paragraph('Question 1 (10 marks):')
rubric.add_paragraph('- 5 marks for correctly defining capital expenditure and revenue expenditure')
rubric.add_paragraph('- 5 marks for giving one appropriate example of each')
rubric.add_paragraph('Question 2 (8 marks):')
rubric.add_paragraph('- 2 marks for identifying the tax invoice requirement')
rubric.add_paragraph('- 2 marks for explaining GST return filing and credit matching')
rubric.add_paragraph('- 2 marks for confirming eligibility of goods/services')
rubric.add_paragraph('- 2 marks for maintaining supporting records')
rubric.add_paragraph('Question 3 (7 marks):')
rubric.add_paragraph('- 4 marks for applying the straight-line depreciation formula')
rubric.add_paragraph('- 3 marks for calculating the correct amount of ₹12,000')
rubric.add_paragraph('Set `needs_human_review` to true if the answer is ambiguous, if the arithmetic is inconsistent, or if the document is partially unreadable.')
rubric.save(base / 'chartered_accountancy_rubric.docx')

student1 = Document()
student1.add_heading('Student Quiz - STU001', level=1)
student1.add_paragraph('1. Explain the difference between capital expenditure and revenue expenditure. Provide one example of each.')
student1.add_paragraph('Capital expenditure is a cost that provides benefits beyond the current accounting period and is capitalized as an asset. Example: purchase of a new machine. Revenue expenditure is an expense for operational activities and is charged in the current period. Example: repair and maintenance expense.')
student1.add_paragraph('2. Describe the key steps in the GST input tax credit claim process for a registered business.')
student1.add_paragraph('The business should obtain a valid tax invoice, verify the eligibility of the purchase, report the amount in the GST return, match the credit with output tax, and retain the invoices and returns for audit.')
student1.add_paragraph('3. Calculate depreciation for machinery purchased for ₹120,000 on 1 April using the straight-line method at 10% per annum for the first year.')
student1.add_paragraph('Depreciation = 120,000 × 10% = 12,000. Therefore, first-year depreciation is ₹12,000.')
student1.save(base / 'student_quiz_001.docx')

student2 = Document()
student2.add_heading('Student Quiz - STU002', level=1)
student2.add_paragraph('1. Explain the difference between capital expenditure and revenue expenditure. Provide one example of each.')
student2.add_paragraph('Capital expenditure is a cost that benefits more than one year, and revenue expenditure is a cost for ongoing business operations. Example of capital expenditure: new furniture. Example of revenue expenditure: salary payment.')
student2.add_paragraph('2. Describe the key steps in the GST input tax credit claim process for a registered business.')
student2.add_paragraph('To claim input tax credit, a registered business must have an invoice, file its GST return, and ensure purchases are eligible. The business must also keep supporting documents for the claim.')
student2.add_paragraph('3. Calculate depreciation for machinery purchased for ₹120,000 on 1 April using the straight-line method at 10% per annum for the first year.')
student2.add_paragraph('Using straight-line method: 120,000 × 10% = 12,000. So depreciation is ₹12,000.')
student2.save(base / 'student_quiz_002.docx')
# Create a small valid PDF using manual PDF syntax.
pdf_path = base / 'student_quiz_003.pdf'
text_lines = [
    '1. Explain the difference between capital expenditure and revenue expenditure. Provide one example of each.',
    'Capital expenditure is for long-term assets; revenue expenditure is for operating expenses.',
    '2. Describe the key steps in the GST input tax credit claim process for a registered business.',
    'Claim requires an invoice, eligible purchase, filing the GST return, and keeping records.',
    '3. Calculate depreciation for machinery purchased for ₹120,000 on 1 April using the straight-line method at 10% per annum for the first year.',
    'Depreciation = 120,000 × 10% = 12,000.'
]

stream_text = "BT\n/F1 12 Tf\n50 760 Td\n"
for line in text_lines:
    stream_text += f"({line}) Tj\n0 -18 Td\n"
stream_text += "ET\n"
stream_bytes = stream_text.encode('utf-8')

header = b"%PDF-1.4\n"
header += b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
header += b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
header += b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n"

obj4 = f"4 0 obj\n<< /Length {len(stream_bytes)} >>\nstream\n".encode('utf-8') + stream_bytes + b"endstream\nendobj\n"

font_obj = b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n"
body = header + obj4 + font_obj

positions = [0]
positions.append(len(header))
positions.append(len(header) + len(obj4))
positions.append(len(header) + len(obj4) + len(font_obj))

xref = b"xref\n0 6\n0000000000 65535 f \n"
for pos in positions[1:]:
    xref += f"{pos:010d} 00000 n \n".encode('utf-8')

trailer = b"trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n"
trailer += str(len(body)).encode('utf-8') + b"\n%%EOF\n"

with open(pdf_path, 'wb') as f:
    f.write(body)
    f.write(xref)
    f.write(trailer)

print(f'Created sample files in {base}')
