from lxml import etree

from flask import Flask, render_template, request, send_from_directory
import os
import pandas as pd
import xml.etree.ElementTree as ET
from xml.dom import minidom

app = Flask(__name__)

UPLOAD_FOLDER = "/mnt/data/uploads"
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def csv_to_xml(csv_path):
    # Load data from CSV file
    data = pd.read_csv(csv_path, header=None)
    num_rows = len(data)

    # Mappings and other variables from the provided script
    trainingprovider_mapping = {
        0: 'tpemail',
        1: 'tpid',
        2: 'tpphone'
    }
    header_mapping = {
        3: 'catalognum',
        12: 'classtype',
        5: 'classcity',
        6: 'classstate',
        7: 'classzipcode',
        8: 'startdate',
        9: 'enddate',
        15: 'numstudent',
        13: 'trainingmethod'
    }
    instructorpoc_mapping = {
        16: 'instlastname',
        17: 'instfirstname',
        18: 'instphone',
        19: 'instemail'
    }
    student_mapping = {
        22: 'sid',
        23: 'studentlastname',
        24: 'studentfirstname',
        25: 'international',
        26: 'studentcity',
        27: 'studentstate',
        28: 'studentzipcode',
        29: 'studentemail',
        30: 'studentphone',
        31: 'govnlevel',
        32: 'discipline'
    }
    question_cols = [33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55]
    comment_cols = [56, 57, 58, 59]
    pretest_col = [20]
    posttest_col = [21]

    # Generate XML from CSV data
    root = ET.Element('Manifest')

    # Iterate over rows of CSV data
    for i in range(1, num_rows):  # Start from row 1
        #Placeholder for XML generation based on your script's logic
        for i in range(1, num_rows):  # Start from row 1

            # Create 'submission' element
            submission = ET.SubElement(root, 'submission')

            # Create 'trainingprovider' element with its attributes
            trainingprovider = ET.SubElement(submission, 'trainingprovider',
                                             {xml_attr: str(data.iloc[i, csv_col]) for csv_col, xml_attr in
                                              trainingprovider_mapping.items()})

            # Create 'class' element with its attributes
            class_element = ET.SubElement(trainingprovider, 'class',
                                          {xml_attr: str(data.iloc[i, csv_col]) for csv_col, xml_attr in
                                           header_mapping.items()})

            # Create 'instructorpoc' elements with their attributes
            # The first 'instructorpoc' uses data from the first row of the group
            instructorpoc1 = ET.SubElement(class_element, 'instructorpoc',
                                           {xml_attr: str(data.iloc[i, csv_col]) for csv_col, xml_attr in
                                            instructorpoc_mapping.items()})

            # The second 'instructorpoc' uses data from the second row of the group
            if i + 1 < len(data):
                instructorpoc2 = ET.SubElement(class_element, 'instructorpoc',
                                               {xml_attr: str(data.iloc[i + 1, csv_col]) for csv_col, xml_attr in
                                                instructorpoc_mapping.items()})

            # Create 'registration' element
            registration = ET.SubElement(class_element, 'registration')

            # Create 'student' elements with their attributes
            # Each 'student' uses data from one of the next NINE rows of the group
            for j in range(0, num_rows):
                if i + j < num_rows:  # Change this line to start from the earlier row
                    student = ET.SubElement(registration, 'student',
                                            {xml_attr: str(data.iloc[i + j, csv_col]) for csv_col, xml_attr in
                                             student_mapping.items()})

            # Create 'evaluations' element
            evaluations = ET.SubElement(class_element, 'evaluations')

            # Iterate over NINE rows for each group
            for j in range(0, num_rows):
                if i + j < num_rows:  # Change this line to start from the earlier row
                    # Create 'evaldata' element
                    evaldata = ET.SubElement(evaluations, 'evaldata')

                    # Create 'question' elements with their attributes
                    for qid, col in enumerate(question_cols, start=1):
                        question = ET.SubElement(evaldata, 'question',
                                                 {'answer': str(data.iloc[i + j, col]), 'id': str(qid)})

                    # Create 'comment' elements with their attributes
                    for cid, col in enumerate(comment_cols, start=24):
                        comment = ET.SubElement(evaldata, 'comment',
                                                {'answer': str(data.iloc[i + j, col]), 'id': str(cid)})

            # Create 'testaverage' element with 'pretest' and 'posttest' attributes
            # The actual data starts from the second row (index 1 if we start counting from 0)
            # We only set the 'pretest' and 'posttest' attributes for the first student of each group
            try:
                pretest_value = float(data.iloc[1, 20])  # Access the pretest value at row 1, column 20
                posttest_value = float(data.iloc[1, 21])  # Access the posttest value at row 1, column 21
                if not pd.isna(pretest_value) and not pd.isna(posttest_value):
                    testaverage = ET.SubElement(class_element, 'testaverage',
                                                {'pretest': str(pretest_value), 'posttest': str(posttest_value)})
            except (ValueError, TypeError):
                pass
        # Convert the XML tree to a string for display
        xml_string = ET.tostring(root, encoding='unicode')

        # Write XML to file
        tree = ET.ElementTree(root)

        # Display XML string
        print(xml_string)

    # Convert the XML tree to a string for display
    xml_string = ET.tostring(root, encoding='unicode')

    # Parse the string with minidom to make it pretty
    dom = minidom.parseString(xml_string)
    pretty_xml = dom.toprettyxml(indent="    ")

    # Define the DOCTYPE declaration and insert it
    doctype = '<!DOCTYPE Manifest SYSTEM "submission.dtd">'
    pretty_xml = pretty_xml.replace('<?xml version="1.0" ?>', f'<?xml version="1.0" ?>\n{doctype}')

    # Return the pretty XML string
    return pretty_xml


@app.route('/')
def index():
    return render_template('upload.html')


def validate_xml_with_dtd(xml_file):
    # Parse the XML file
    parser = etree.XMLParser(dtd_validation=True)
    try:
        with open(xml_file, 'r') as file:
            etree.parse(file, parser)
        return True, "The XML file is valid against the DTD."
    except etree.XMLSyntaxError as e:
        return False, str(e)


@app.route('/upload', methods=['POST'])
def upload_file_with_validation():
    if 'file' not in request.files:
        return "No file part"

    file = request.files['file']
    if file.filename == '':
        return "No selected file"

    # Check if the uploaded file is a CSV
    if not file.filename.endswith(".csv"):
        return "Please upload a valid CSV file."

    # Save the uploaded CSV file
    csv_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(csv_path)

    # Convert the CSV to XML
    xml_content = csv_to_xml(csv_path)

    # Save the XML content to a file
    xml_filename = file.filename.replace(".csv", ".xml")
    xml_path = os.path.join(app.config['UPLOAD_FOLDER'], xml_filename)
    with open(xml_path, 'w', encoding='utf-8') as xml_file:
        xml_file.write(xml_content)

    # Validate the XML file against the DTD
    is_valid, validation_message = validate_xml_with_dtd(xml_path)

    # Provide feedback to the user
    if is_valid:
        return f'File uploaded and converted successfully! The XML is valid against the DTD. <a href="/download/{xml_filename}">Download XML</a>'
    else:
        return f'File uploaded and converted, but the XML is NOT valid against the DTD. Reason: {validation_message}. <a href="/download/{xml_filename}">Download XML</a>'


@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)


if __name__ == "__main__":
    app.run()
