import glob

def merge_route_files(input_folder, output_file):
    # Lista todos os arquivos .rou.xml do diretório
    files = glob.glob(f"{input_folder}/*.rou.xml")

    with open(output_file, "w") as outfile:
        # Escreve cabeçalho e abre a tag <routes>
        outfile.write('<routes>\n')

        for file in files:
            with open(file, "r") as infile:
                for line in infile:
                    line = line.strip()
                    # Ignora cabeçalhos XML e tags <routes> dos arquivos individuais
                    if line.startswith('<?xml') or line == '<routes>' or line == '</routes>':
                        continue
                    outfile.write(line + '\n')

        # Fecha a tag <routes> no final
        outfile.write('</routes>\n')

    print(f"Merged {len(files)} files into {output_file}")

# Use assim:
merge_route_files("routes", "routes/combined.rou.xml")
