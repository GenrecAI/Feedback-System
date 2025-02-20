import matplotlib.pyplot as plt
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.platypus import KeepTogether
import io

def create_score_graph(feedback_data):
    """Create a prominent bar graph of total scores."""
    # Prepare data for plotting
    references = []
    totals = []
    
    for staff_data in feedback_data.values():
        references.append(staff_data['reference'])
        totals.append(sum(staff_data['scores']))
    
    # Set figure parameters for high quality
    plt.rcParams['figure.dpi'] = 300
    plt.rcParams['font.size'] = 10
    
    # Create large figure with white background
    plt.figure(figsize=(10, 6), facecolor='white')
    ax = plt.gca()
    ax.set_facecolor('white')
    
    # Create bold blue bars with generous spacing
    bars = plt.bar(references, totals, color='#0000FF', width=0.6)
    
    # Customize the plot
    plt.ylim(0, 120)
    plt.yticks(range(0, 121, 20))
    plt.grid(True, axis='y', linestyle='--', alpha=0.7, color='lightgrey')
    
    # Remove border
    for spine in plt.gca().spines.values():
        spine.set_visible(False)
    
    # Bold labels
    plt.xlabel('Staff References', fontsize=10, fontweight='bold')
    plt.ylabel('Total Score', fontsize=10, fontweight='bold')
    
    # Add value labels on top of bars
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.1f}',
                ha='center', va='bottom')
    
    # Tight layout to maximize graph size
    plt.tight_layout()
    
    # Save to bytes buffer
    img_buffer = io.BytesIO()
    plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight', transparent=False)
    img_buffer.seek(0)
    plt.close()
    
    return img_buffer

def split_questions_into_columns(questions, num_columns=3):
    """Split questions into columns for space-efficient layout."""
    col_length = (len(questions) + num_columns - 1) // num_columns
    columns = []
    
    for i in range(0, len(questions), col_length):
        columns.append(questions[i:i + col_length])
    
    return columns

def generate_feedback_report(academic_year, branch, semester, year, feedback_data):
    """Generate a single-page PDF report with prominent graph."""
    # Create PDF document with minimal margins
    doc = SimpleDocTemplate(
        f"feedback_report_{branch}_{semester}.pdf",
        pagesize=A4,
        rightMargin=25,
        leftMargin=25,
        topMargin=25,
        bottomMargin=25
    )

    # Styles
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
        fontSize=7,
        leading=8  # Minimal line spacing
    )

    # Document elements
    elements = []

    # Compact header
    elements.append(Paragraph("V.S.B. ENGINEERING COLLEGE, KARUR", title_style))
    elements.append(Paragraph("(An Autonomous Institution)", subtitle_style))
    elements.append(Paragraph("STUDENT'S FEEDBACK ON COURSE DELIVERY", subtitle_style))

    # Single-line academic details
    academic_info = f"Academic year: {academic_year}    Branch: {branch}    Semester: {semester}    Year: {year}"
    academic_info = academic_info.replace("    ", " " * int((A4[0] - 50) // len(academic_info)))
    elements.append(Paragraph(academic_info, info_style))
    elements.append(Spacer(1, 5))

    # Compact table
    table_data = [
        ['Staff Name', 'Subject'] + [f'Q{i}' for i in range(1, 11)] + ['Total']
    ]

    for staff_name, data in feedback_data.items():
        scores = data['scores']
        total = sum(scores)
        row = [
            f"{staff_name} ({data['reference']})",
            data['subject']
        ] + [f"{score:.1f}" for score in scores] + [f"{total:.1f}"]
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
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 3),
        ('RIGHTPADDING', (0, 0), (-1, -1), 3),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 10))

    # Prominent graph
    graph_buffer = create_score_graph(feedback_data)
    img = Image(graph_buffer)
    # Set width to 80% of page width
    img.drawWidth = A4[0] * 0.8
    # Scale height proportionally but target about 4 inches
    img.drawHeight = 4 * inch
    elements.append(img)
    elements.append(Spacer(1, 10))

    # Questions in three columns
    questions = [
        "1. How is the faculty's approach?",
        "2. How has the faculty prepared for the classes?",
        "3. Does the faculty inform you about your expected competencies, course outcomes?",
        "4. How often does the faculty illustrate the concepts through examples and practical applications?",
        "5. Whether faculty covers syllabus in time?",
        "6. Do you agree that the faculty teaches content beyond syllabus?",
        "7. How does the faculty communicate?",
        "8. Whether faculty returns answer scripts in time and produce helpful comments?",
        "9. How does the faculty identify your strengths and encourage you with high level of challenges?",
        "10. How does the faculty counsel & encourage the Students?"
    ]
    
    # Split questions into three columns
    question_columns = split_questions_into_columns(questions)
    question_table_data = list(zip(*question_columns))
    
    # Create table for questions
    question_table = Table(question_table_data, colWidths=[doc.width/3.1]*3)
    question_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 7),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    elements.append(question_table)

    # Signature line at bottom
    signature_style = ParagraphStyle(
        'SignatureStyle',
        parent=styles['Normal'],
        fontSize=8,
        alignment=1
    )
    elements.append(Spacer(1, 10))
    elements.append(Paragraph("Class Advisor                    HOD                    Principal", signature_style))

    # Build PDF
    doc.build(elements)

if __name__ == "__main__":
    # Example data
    sample_data = {
        "Mrs.V.Sheela": {
            "reference": "S1",
            "subject": "23HST201 - Professional English II",
            "scores": [9.3, 9.3, 9.5, 9.7, 9.2, 9.4, 9.2, 9.5, 9.7, 9.6]
        }
    }

    generate_feedback_report(
        academic_year="2024-25",
        branch="Computer Science and Engineering",
        semester="EVEN",
        year="II",
        feedback_data=sample_data
    )