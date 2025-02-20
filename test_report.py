from report_generator import generate_feedback_report

# Sample data with multiple staff members to demonstrate compact layout
sample_data = {
    "Mrs.V.Sheela": {
        "reference": "S1",
        "subject": "23HST201 - Professional English II",
        "scores": [9.3, 9.3, 9.5, 9.7, 9.2, 9.4, 9.2, 9.5, 9.7, 9.6]
    },
    "Dr.K.Prakash": {
        "reference": "S2",
        "subject": "23CSC201 - Data Structures",
        "scores": [9.1, 9.4, 9.2, 9.6, 9.3, 9.5, 9.4, 9.2, 9.3, 9.5]
    },
    "Dr.R.Kumar": {
        "reference": "S3",
        "subject": "23MAT201 - Mathematics II",
        "scores": [9.4, 9.2, 9.5, 9.3, 9.6, 9.4, 9.5, 9.3, 9.4, 9.2]
    },
    "Dr.S.Ramesh": {
        "reference": "S4",
        "subject": "23PHY201 - Physics",
        "scores": [8.9, 9.1, 9.3, 9.2, 9.4, 9.0, 9.2, 9.1, 9.3, 9.0]
    },
    "Prof.M.Anand": {
        "reference": "S5",
        "subject": "23CSC202 - Computer Networks",
        "scores": [9.5, 9.6, 9.4, 9.7, 9.3, 9.5, 9.6, 9.4, 9.5, 9.7]
    },
    "Dr.P.Senthil": {
        "reference": "S6",
        "subject": "23CSC203 - Database Systems",
        "scores": [9.2, 9.3, 9.1, 9.4, 9.2, 9.5, 9.3, 9.2, 9.4, 9.1]
    },
    "Dr.L.Priya": {
        "reference": "S7",
        "subject": "23CSC204 - Operating Systems",
        "scores": [9.6, 9.5, 9.7, 9.4, 9.6, 9.3, 9.5, 9.6, 9.4, 9.5]
    },
    "Mrs.K.Lakshmi": {
        "reference": "S8",
        "subject": "23CSC205 - Software Engineering",
        "scores": [9.3, 9.4, 9.2, 9.5, 9.3, 9.6, 9.4, 9.3, 9.5, 9.4]
    }
}

# Generate the report with compact single-page layout
generate_feedback_report(
    academic_year="2024-25",
    branch="Computer Science and Engineering",
    semester="EVEN",
    year="II",
    feedback_data=sample_data
)

print("Report generated successfully! Check feedback_report_Computer Science and Engineering_EVEN.pdf")