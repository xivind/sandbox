import csv
import sqlite3
import os

def create_database(csv_file, db_file):
    """
    Create a SQLite database from the given CSV file
    """
    # Remove the database file if it already exists
    if os.path.exists(db_file):
        os.remove(db_file)
    
    # Connect to the database
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    # Create the schema
    cursor.executescript('''
    -- Main table for regulatory information
    CREATE TABLE reguleringer (
      id INTEGER PRIMARY KEY,
      informasjonstype TEXT,
      navn TEXT NOT NULL,
      ingress TEXT,
      beskrivelse TEXT,
      kontekstavhengig_beskrivelse TEXT,
      normeringsniva TEXT,
      eif_niva TEXT,
      status TEXT,
      ansvarlig TEXT,
      referanse_lenketekst TEXT,
      referanse_url TEXT
    );
    
    -- Table for component information
    CREATE TABLE komponenter (
      id INTEGER PRIMARY KEY,
      informasjonstype TEXT,
      navn TEXT NOT NULL,
      ingress TEXT,
      beskrivelse TEXT,
      kontekstavhengig_beskrivelse TEXT,
      normeringsniva TEXT,
      eif_niva TEXT,
      status TEXT,
      ansvarlig TEXT,
      referanse_lenketekst TEXT,
      referanse_url TEXT
    );

    -- Table for collaboration services (samhandlingstjenester)
    CREATE TABLE samhandlingstjeneter (
      id INTEGER PRIMARY KEY,
      name TEXT UNIQUE NOT NULL
    );

    -- Junction table to represent the many-to-many relationship 
    -- between reguleringer and services
    CREATE TABLE koblinger (
      entity_id INTEGER,
      entity_type TEXT,  -- 'regulering' or 'komponent'
      samhandlingstjeneste_id INTEGER,
      PRIMARY KEY (entity_id, entity_type, samhandlingstjeneste_id),
      FOREIGN KEY (samhandlingstjeneste_id) REFERENCES samhandlingstjeneter(id) ON DELETE CASCADE
    );

    -- Indexes for better query performance
    CREATE INDEX idx_reguleringer_type ON reguleringer(informasjonstype);
    CREATE INDEX idx_reguleringer_status ON reguleringer(status);
    CREATE INDEX idx_reguleringer_ansvarlig ON reguleringer(ansvarlig);
    
    CREATE INDEX idx_komponenter_type ON komponenter(informasjonstype);
    CREATE INDEX idx_komponenter_status ON komponenter(status);
    CREATE INDEX idx_komponenter_ansvarlig ON komponenter(ansvarlig);
    ''')
    
    # Dictionary to store service names and their IDs
    services_dict = {}
    
    # List of informasjonstype values for komponenter
    komponent_types = [
        "Nasjonal e-helseløsning", 
        "Teknisk grensesnitt", 
        "Samhandlingskomponent", 
        "Informasjonslager", 
        "Informasjonstjeneste"
    ]
    
    # Read the CSV file
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        # Process each row
        for row in reader:
            info_type = row['informasjonstype'].strip()
            
            # Determine which table to insert into
            if info_type in komponent_types:
                # Insert into komponenter table
                cursor.execute('''
                INSERT INTO komponenter 
                (informasjonstype, navn, ingress, beskrivelse, kontekstavhengig_beskrivelse, 
                 normeringsniva, eif_niva, status, ansvarlig, referanse_lenketekst, referanse_url)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    info_type,
                    row['navn'].strip(),
                    row['ingress'].strip() if row['ingress'] else None,
                    row['beskrivelse'].strip() if row['beskrivelse'] else None,
                    row['kontekstavhengig_beskrivelse'].strip() if row['kontekstavhengig_beskrivelse'] else None,
                    row['normeringsniva'].strip() if row['normeringsniva'] else None,
                    row['eif_niva'].strip() if row['eif_niva'] else None,
                    row['status'].strip() if row['status'] else None,
                    row['ansvarlig'].strip() if row['ansvarlig'] else None,
                    row['referanse_lenketekst'].strip() if row['referanse_lenketekst'] else None,
                    row['referanse_url'].strip() if row['referanse_url'] else None
                ))
                entity_id = cursor.lastrowid
                entity_type = 'komponent'
            else:
                # Insert into reguleringer table
                cursor.execute('''
                INSERT INTO reguleringer 
                (informasjonstype, navn, ingress, beskrivelse, kontekstavhengig_beskrivelse, 
                 normeringsniva, eif_niva, status, ansvarlig, referanse_lenketekst, referanse_url)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    info_type,
                    row['navn'].strip(),
                    row['ingress'].strip() if row['ingress'] else None,
                    row['beskrivelse'].strip() if row['beskrivelse'] else None,
                    row['kontekstavhengig_beskrivelse'].strip() if row['kontekstavhengig_beskrivelse'] else None,
                    row['normeringsniva'].strip() if row['normeringsniva'] else None,
                    row['eif_niva'].strip() if row['eif_niva'] else None,
                    row['status'].strip() if row['status'] else None,
                    row['ansvarlig'].strip() if row['ansvarlig'] else None,
                    row['referanse_lenketekst'].strip() if row['referanse_lenketekst'] else None,
                    row['referanse_url'].strip() if row['referanse_url'] else None
                ))
                entity_id = cursor.lastrowid
                entity_type = 'regulering'
            
            # Process samhandlingstjenester (comma-separated values)
            if row['samhandlingstjenester']:
                # Strip quotes if they exist
                services_raw = row['samhandlingstjenester']
                if services_raw.startswith('"') and services_raw.endswith('"'):
                    services_raw = services_raw[1:-1]
                
                services = [s.strip() for s in services_raw.split(',')]
                
                for service in services:
                    # Add service if it doesn't exist
                    if service not in services_dict:
                        cursor.execute('INSERT INTO samhandlingstjeneter (name) VALUES (?)', (service,))
                        services_dict[service] = cursor.lastrowid
                    
                    # Link entity to service
                    cursor.execute('''
                    INSERT INTO koblinger (entity_id, entity_type, samhandlingstjeneste_id)
                    VALUES (?, ?, ?)
                    ''', (entity_id, entity_type, services_dict[service]))
    
    # Commit the changes
    conn.commit()
    
    # Print some statistics
    cursor.execute('SELECT COUNT(*) FROM reguleringer')
    reguleringer_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM komponenter')
    komponenter_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM samhandlingstjeneter')
    service_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM koblinger')
    link_count = cursor.fetchone()[0]
    
    print(f"Database created successfully with:")
    print(f"- {reguleringer_count} reguleringer")
    print(f"- {komponenter_count} komponenter")
    print(f"- {service_count} unique samhandlingstjeneter")
    print(f"- {link_count} koblinger")
    
    # Close the connection
    conn.close()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 3:
        print("Usage: python csv_to_sqlite.py input.csv output.db")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    db_file = sys.argv[2]
    
    create_database(csv_file, db_file)