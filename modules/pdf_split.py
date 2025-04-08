import os
import PyPDF2


def split_pdf(pdf_path, split_page, part1_name, part2_name):
    """"
    Splits a PDF file into two parts at the specified page number.
    """
    # Open the PDF file in read-binary mode.
    with open(pdf_path, 'rb') as infile:
        reader = PyPDF2.PdfReader(infile)
        total_pages = len(reader.pages)
        
        # Validate the split page number.
        if split_page < 1 or split_page > total_pages:
            raise ValueError(f"split_page must be between 1 and the total number of pages ({total_pages})")
        
        # Create PDF writers for the two parts.
        writer1 = PyPDF2.PdfWriter()
        writer2 = PyPDF2.PdfWriter()
        
        # Pages 0 to split_page-1 go to the first part.
        for i in range(split_page):
            writer1.add_page(reader.pages[i])
        
        # Pages split_page to end go to the second part.
        for i in range(split_page, total_pages):
            writer2.add_page(reader.pages[i])
        
        # Save the new PDFs in the same directory as the input PDF.
        directory = os.path.dirname(pdf_path)
        output1 = os.path.join(directory, part1_name)
        output2 = os.path.join(directory, part2_name)
        
        with open(output1, 'wb') as out1:
            writer1.write(out1)
        with open(output2, 'wb') as out2:
            writer2.write(out2)
        
        print("PDF split successfully!")
        print(f"First part saved as: {output1}")
        print(f"Second part saved as: {output2}")

if __name__ == '__main__': # This block is executed when the script is run directly.
    # User inputs.
    pdf_path = input("Enter the PDF file path: ").strip()
    
    try:
        # The split_page is the first page of the second PDF.
        split_page = int(input("Enter the page number where to split (first page of second PDF): ").strip())
    except ValueError:
        print("Invalid page number.")
        exit(1)
    
    part1_name = input("Enter the name for the first part (e.g., part1.pdf): ").strip()
    part2_name = input("Enter the name for the second part (e.g., part2.pdf): ").strip()
    
    try:
        split_pdf(pdf_path, split_page, part1_name, part2_name)
    except Exception as e:
        print(f"An error occurred: {e}")


