from flask import Flask, request, jsonify, render_template
from PIL import Image, ImageOps
import ezdxf
import os

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def home():
    return render_template('index.html')

def hex_to_rgb(hex_color):
    """Convertit une couleur hexadécimale (#RRGGBB) en tuple RGB."""
    if not hex_color.startswith("#") or len(hex_color) != 7:
        raise ValueError("Couleur hexadécimale invalide.")
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def image_to_dxf(input_file, output_file, color_to_remove):
    try:
        img = Image.open(input_file).convert("RGB")  # Charger l'image en mode RGB
        pixels = img.load()
        width, height = img.size

        # Supprimer la couleur spécifiée en la rendant blanche
        for y in range(height):
            for x in range(width):
                if pixels[x, y] == color_to_remove:
                    pixels[x, y] = (255, 255, 255)  # Remplacer par blanc

        # Convertir l'image en mode binaire (noir et blanc)
        img = img.convert("L")  # Convertir en niveaux de gris
        img = img.point(lambda x: 0 if x < 128 else 255, '1')  # Binariser

        # Inverser l'image pour que les parties noires soient converties
        img = ImageOps.invert(img.convert("L")).convert("1")

        # Créer le fichier DXF
        doc = ezdxf.new()
        msp = doc.modelspace()
        pixels = img.load()

        for y in range(height):
            for x in range(width):
                if pixels[x, y] == 0:  # Si le pixel est noir
                    msp.add_lwpolyline([
                        (x, height - y),
                        (x + 1, height - y),
                        (x + 1, height - (y + 1)),
                        (x, height - (y + 1)),
                        (x, height - y)
                    ], close=True)

        doc.saveas(output_file)
        return output_file
    except Exception as e:
        return str(e)

@app.route('/convert', methods=['POST'])
def convert():
    if 'file' not in request.files or 'color' not in request.form:
        return jsonify({"error": "Fichier ou couleur manquant"})
    
    file = request.files['file']
    hex_color = request.form['color']  # Par exemple, "#ffffff"
    
    if file.filename == '':
        return jsonify({"error": "Aucun fichier sélectionné"})
    
    try:
        rgb_color = hex_to_rgb(hex_color)  # Convertit en (255, 255, 255)
    except ValueError as e:
        return jsonify({"error": f"Couleur invalide : {hex_color}. Erreur : {str(e)}"})

    # Crée les chemins pour les fichiers
    input_path = os.path.join(UPLOAD_FOLDER, file.filename)
    output_path = os.path.splitext(input_path)[0] + "_convertie.dxf"
    
    # Sauvegarde le fichier
    file.save(input_path)

    # Appelle la fonction de conversion
    result = image_to_dxf(input_path, output_path, rgb_color)
    if os.path.exists(result):
        return jsonify({"message": f"Fichier DXF généré : {result}"})
    else:
        return jsonify({"error": f"Erreur lors de la conversion : {result}"})

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5001)

port = int(os.environ.get("PORT", 5001))
app.run(host="0.0.0.0", port=port)

