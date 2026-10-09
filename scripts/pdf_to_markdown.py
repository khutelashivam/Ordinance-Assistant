"""Turn the project PDF into topic-based Markdown files."""

import os
import re
import sys

PROJECT_FOLDER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_FOLDER not in sys.path:
    sys.path.insert(0, PROJECT_FOLDER)

import pymupdf

from services.settings import KNOWLEDGE_SOURCE_FOLDER, PDF_PATH


TOPICS = {
    1: "Overview",
    2: "Department Undergraduate Program Committee (DUPC)",
    3: "Institute Undergraduate Program Committee (IUPC)",
    4: "Academic Affairs",
    5: "Academic Calendar",
    6: "Admission",
    7: "Registration",
    8: "Attendance",
    9: "Leave of Absence",
    10: "Residence",
    11: "Course Structure",
    12: "Credit Requirement and Course Load",
    13: "Major-Minor",
    14: "Honours Degree",
    15: "Examination",
    16: "Summer School",
    17: "Grading System",
    18: "Evaluation Process",
    19: "Method of awarding letter grades",
    20: "Examination Unfair Means Committee (EUMC)",
    21: "Duration of the Programme",
    22: "Termination from the programme",
    23: "Withholding of Grades",
    24: "Eligibility for the Award of B.Tech Degree",
    25: "Institute Medals and Prizes",
    26: "Conduct and Disciplines",
    27: "Other Matters: Legal",
}

TOPIC_HEADING = re.compile(r"^(\d{1,2})\.\s+(.+)$")
CLAUSE_HEADING = re.compile(r"^(\d+(?:\.\d+)+)\.?\s*(.*)$")


def save_section(topic, section):
    """Add a finished section to its topic."""
    if section:
        text = "\n".join(section["lines"]).strip()
        if text:
            topic["sections"].append({
                "name": section["name"],
                "page": ", ".join(str(page) for page in sorted(section["pages"])),
                "text": text,
            })


def main():
    """Read the local PDF and write the Markdown knowledge files."""
    pdf = pymupdf.open(PDF_PATH)
    topics = []
    current_topic = None
    current_section = None
    page_number = 1

    # The first two PDF pages are the cover and contents page.
    for pdf_page in range(2, len(pdf)):
        for source_line in pdf[pdf_page].get_text().splitlines():
            line = source_line.strip()
            if not line:
                if current_section:
                    current_section["lines"].append("")
                continue

            if line.startswith("Page ") and " of " in line:
                page_number = int(line.split()[1])
                continue
            if line in ("IIIT Bhagalpur B.Tech Ordinances", "Ordinance", "Regulations"):
                continue

            topic_match = TOPIC_HEADING.match(line)
            if topic_match:
                number = int(topic_match.group(1))
                title = topic_match.group(2).strip()
                if TOPICS.get(number, "").lower() == title.lower():
                    if current_section:
                        save_section(current_topic, current_section)
                    current_topic = {"number": number, "title": title, "sections": []}
                    topics.append(current_topic)
                    current_section = {"name": str(number), "pages": set(), "lines": []}
                    continue

            if line == "Appendix-A":
                if current_section:
                    save_section(current_topic, current_section)
                current_topic = {
                    "number": 28,
                    "title": "Appendix A - Unfair Means Form",
                    "sections": [],
                }
                topics.append(current_topic)
                current_section = {"name": "Appendix-A", "pages": set(), "lines": []}
                continue

            if current_topic:
                clause = CLAUSE_HEADING.match(line)
                if clause and clause.group(1).split(".")[0] == str(current_topic["number"]):
                    save_section(current_topic, current_section)
                    current_section = {
                        "name": clause.group(1),
                        "pages": {page_number},
                        "lines": [clause.group(2)] if clause.group(2) else [],
                    }
                elif current_section:
                    current_section["lines"].append(line)
                    current_section["pages"].add(page_number)

    if current_section:
        save_section(current_topic, current_section)

    os.makedirs(KNOWLEDGE_SOURCE_FOLDER, exist_ok=True)
    for topic in topics:
        file_slug = re.sub(r"[^a-z0-9]+", "_", topic["title"].lower()).strip("_")
        file_name = "section_" + str(topic["number"]).zfill(2) + "_" + file_slug + ".md"
        file_path = os.path.join(KNOWLEDGE_SOURCE_FOLDER, file_name)

        with open(file_path, "w", encoding="utf-8") as file:
            file.write("# " + topic["title"] + "\n\n")
            for section in topic["sections"]:
                file.write("## " + section["name"] + "\n")
                file.write("<!-- source-pages: " + section["page"] + " -->\n\n")
                file.write(section["text"] + "\n\n")

    print("Created " + str(len(topics)) + " topic Markdown files from " + PDF_PATH)


if __name__ == "__main__":
    main()
