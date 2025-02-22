import matplotlib.pyplot as plt
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.platypus import KeepTogether
import io
import os
import csv

def read_feedback_data(department, semester):
    """Read and process feedback data from mainrating.csv"""
    feedback_data = {}
    ref_count = 1
    
    print(f"\nReading feedback data for {department}, Semester {semester}...")
    with open('mainrating.csv', 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row['department'] == department and row['semester'] == str(semester):
                # Create unique key combining staff and subject
                key = f"{row['staff']}_{row['subject']}"
                feedback_data[key] = {
                    "reference": f"S{ref_count}",
                    "staff_name": row['staff'],
                    "subject": row['subject'],
                    "scores": [
                        float(row['q1_avg']), float(row['q2_avg']),
                        float(row['q3_avg']), float(row['q4_avg']),
                        float(row['q5_avg']), float(row['q6_avg']),
                        float(row['q7_avg']), float(row['q8_avg']),
                        float(row['q9_avg']), float(row['q10_avg'])
                    ]
                }
                print(f"Found data for {row['staff']} teaching {row['subject']}")
                ref_count += 1
    
    print(f"Total {len(feedback_data)} staff-subject combinations processed")
    return feedback_data

def create_score_graph(feedback_data):
    """Create a prominent bar graph of total scores."""
    # Prepare data for plotting
    references = []
    totals = []
    
    for data in feedback_data.values():
        references.append(data['reference'])
        totals.append(sum(data['scores'])/10)  # Average score
    
    # Set figure parameters for high quality
    plt.rcParams['figure.dpi'] = 300
    plt.rcParams['font.size'] = 10
    
    # Create large figure with white background
    plt.figure(figsize=(10, 6), facecolor='white')
    ax = plt.gca()
    ax.set_facecolor('white')
    
    # Create bars with teal green color
    teal_green = '#008080'  # Classic teal color
    bars = plt.bar(references, totals, color=teal_green, width=0.6)
    
    # Customize the plot
    plt.ylim(0, 10)  # Set y-axis limit to 10 since these are averages
    plt.yticks(range(0, 11, 2))  # Ticks at 0, 2, 4, 6, 8, 10
    plt.grid(True, axis='y', linestyle='--', alpha=0.7, color='lightgrey')
    
    # Remove border
    for spine in plt.gca().spines.values():
        spine.set_visible(False)
    
    # Bold labels
    plt.xlabel('Staff References', fontsize=10, fontweight='bold')
    plt.ylabel('Average Score', fontsize=10, fontweight='bold')
    
    # Add value labels on top of bars
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.2f}',
                ha='center', va='bottom')
    
    # Tight layout to maximize graph size
    plt.tight_layout()
    
    # Save to bytes buffer
    img_buffer = io.BytesIO()
    plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight', transparent=False)
    img_buffer.seek(0)
    plt.close()
    
    return img_buffer

def generate_feedback_report(academic_year, branch, semester, year, feedback_data):
    """Generate a single-page PDF report with prominent graph."""
    # Create filename and get absolute path
    filename = f"feedback_report_{branch}_Semester {semester}.pdf"
    filepath = os.path.abspath(filename)
    print(f"\nGenerating feedback report...")
    print(f"Output file will be saved as: {filepath}")
    
    # Create PDF document with minimal margins
    doc = SimpleDocTemplate(
        filename,
        pagesize=A4,
        rightMargin=25,
        leftMargin=25,
        topMargin=25,
        bottomMargin=25
    )

    # Styles and elements setup...
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=12,
        alignment=1,
        spaceAfter=2
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubTitle',
        parent=styles['Normal'],
        fontSize=10,
        alignment=1,
        spaceAfter=2
    )
    
    info_style = ParagraphStyle(
        'InfoStyle',
        parent=styles['Normal'],
        fontSize=9,
        alignment=1,
        spaceAfter=4
    )
    
    question_style = ParagraphStyle(
        'QuestionStyle',
        parent=styles['Normal'],
        fontSize=9,
        leading=10,
        leftIndent=0
    )
    
    reference_title_style = ParagraphStyle(
        'ReferenceTitle',
        parent=styles['Normal'],
        fontSize=10,
        leading=12,
        fontName='Helvetica-Bold'
    )
    
    reference_style = ParagraphStyle(
        'ReferenceStyle',
        parent=styles['Normal'],
        fontSize=9,
        leading=10,
        leftIndent=30
    )
    
    # Document elements
    elements = []

    print("Creating document header...")
    # Compact header
    elements.append(Paragraph("V.S.B. ENGINEERING COLLEGE, KARUR", title_style))
    elements.append(Paragraph("(An Autonomous Institution)", subtitle_style))
    elements.append(Paragraph("STUDENT'S FEEDBACK ON COURSE DELIVERY", subtitle_style))

    # Single-line academic details
    academic_info = f"Academic year: {academic_year}    Branch: {branch}    Semester: {semester}    Year: {year}"
    academic_info = academic_info.replace("    ", " " * int((A4[0] - 50) // len(academic_info)))
    elements.append(Paragraph(academic_info, info_style))
    elements.append(Spacer(1, 5))

    print("Creating feedback data table...")
    # Compact table
    table_data = [
        ['Staff Name', 'Subject'] + [f'Q{i}' for i in range(1, 11)] + ['Total']
    ]

    for key, data in feedback_data.items():
        scores = data['scores']
        total = sum(scores)/10  # Calculate average
        row = [
            data['staff_name'],
            data['subject']
        ] + [f"{score:.2f}" for score in scores] + [f"{total:.2f}"]
        table_data.append(row)

    table = Table(table_data)
    table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),  # Header font
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),  # Content font
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('ALIGN', (0, 0), (1, -1), 'LEFT'),
        ('ALIGN', (2, 0), (-1, -1), 'CENTER'),
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('LEFTPADDING', (0, 0), (-1, -1), 3),
        ('RIGHTPADDING', (0, 0), (-1, -1), 3),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 5))

    print("Generating score graph...")
    # Graph with reduced height
    graph_buffer = create_score_graph(feedback_data)
    img = Image(graph_buffer)
    # Set width to 80% of page width
    img.drawWidth = A4[0] * 0.8
    # Scale height proportionally but keep small for single page
    img.drawHeight = 2.3 * inch
    elements.append(img)
    elements.append(Spacer(1, 5))

    print("Adding references and questions...")
    # References Section
    elements.append(Paragraph("References:", reference_title_style))
    elements.append(Spacer(1, 2))
    
    # Add staff references one per line
    for key, data in feedback_data.items():
        reference_line = f"{data['reference']}: {data['staff_name']} - {data['subject']}"
        elements.append(Paragraph(reference_line, reference_style))
    
    elements.append(Spacer(1, 5))

    # Questions Section (single column)
    questions_text = [
        "Question  1: How is the faculty's approach?",
        "Question  2: How has the faculty prepared for the classes?",
        "Question  3: Does the faculty inform you about your expected competencies, course outcomes?",
        "Question  4: How often does the faculty illustrate the concepts through examples and practical applications?",
        "Question  5: Whether faculty covers syllabus in time?",
        "Question  6: Do you agree that the faculty teaches content beyond syllabus?",
        "Question  7: How does the faculty communicate?",
        "Question  8: Whether faculty returns answer scripts in time and produce helpful comments?",
        "Question  9: How does the faculty identify your strengths and encourage you with high level of challenges?",
        "Question  10: How does the faculty counsel & encourage the Students?"
    ]
    
    # Add questions in single column
    for question in questions_text:
        elements.append(Paragraph(question, question_style))
    
    # Add extra space after questions to push signatures to bottom
    elements.append(Spacer(1, 0.8 * inch))
    
    print("Adding signature section...")
    # Create signature table for even spacing
    signature_table = Table(
        [["Class Advisor", "HOD", "Principal"]],
        colWidths=[doc.width/3.0]*3,
        style=TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
            ('GRID', (0, 0), (-1, -1), 0, colors.white),
        ])
    )
    elements.append(signature_table)

    # Build PDF
    print("\nBuilding final PDF...")
    doc.build(elements)
    print(f"Report generation complete!")
    print(f"Report saved at: {filepath}")

if __name__ == "__main__":
    department = "Computer Science and Business Systems"
    semester = 4
    
    print("\nStarting feedback report generation...")
    print(f"Department: {department}")
    print(f"Semester: {semester}")
    
    # Read data from mainrating.csv
    feedback_data = read_feedback_data(department, semester)

    generate_feedback_report(
        academic_year="2024-25",
        branch=department,
        semester=semester,
        year="II",
        feedback_data=feedback_data
    )