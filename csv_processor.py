import csv
import codecs
import chardet

def convert_csv(input_file, output_file):
    # First, detect the encoding of the input file
    with open(input_file, 'rb') as f:
        result = chardet.detect(f.read())
    
    detected_encoding = result['encoding']
    print(f"Detected encoding: {detected_encoding} with confidence {result['confidence']}")
    
    # These are the columns we want to keep
    columns_to_keep = [
        'informasjonstype', 'navn', 'ingress', 'beskrivelse', 
        'kontekstavhengig_beskrivelse', 'normeringsniva', 'eif_niva', 
        'status', 'samhandlingstjenester', 'ansvarlig', 
        'referanse_lenketekst', 'referanse_url'
    ]
    
    # Open the input file with detected encoding
    with codecs.open(input_file, 'r', encoding=detected_encoding, errors='replace') as input_csv:
        reader = csv.DictReader(input_csv)
        
        # Open the output file with UTF-8 encoding
        with codecs.open(output_file, 'w', encoding='utf-8') as output_csv:
            # Create a writer with only the columns we want to keep
            writer = csv.DictWriter(output_csv, fieldnames=columns_to_keep)
            writer.writeheader()
            
            # Process each row, keeping only the specified columns
            for row in reader:
                filtered_row = {column: row.get(column, '') for column in columns_to_keep}
                writer.writerow(filtered_row)
    
    print(f"Conversion complete. Output saved to {output_file}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 3:
        print("Usage: python csv_converter.py input.csv output.csv")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    convert_csv(input_file, output_file)