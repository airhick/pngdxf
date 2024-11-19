from flask import Flask, request, jsonify, render_template, send_file
from PIL import Image, ImageOps
import ezdxf
import os

app = Flask(__name__)

# Créer un dossier pour les téléchargements si nécessaire
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def home():
    """Page d'accueil."""
    return render_template('index.html')

def hex_to_rgb(hex_color):
    """Convertit une couleur hexadécimale (#RRGGBB) en tuple RGB."""
    try:
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
    except ValueError:
        raise ValueError(f"Couleur hexadécimale invalide : {hex_color}")

def image_to_dxf(input_file, output_file, color_to_remove):
    """Convertir une image PNG en fichier DXF."""
    try:
        # Charger l'image
        img = Image.open(input_file).convert("RGB")
        pixels = img.load()
        width, height = img.size

        # Supprimer la couleur spécifiée
        for y in range(height):
            for x in range(width):
                if pixels[x, y] == color_to_remove:
                    pixels[x, y] = (255, 255, 255)

        # Convertir en noir et blanc
        img = img.convert("L")  # Niveaux de gris
        img = img.point(lambda x: 0 if x < 128 else 255, '1')

        # Inverser pour générer des données DXF
        img = ImageOps.invert(img.convert("L")).convert("1")
        pixels = img.load()

        # Création du fichier DXF
        doc = ezdxf.new()
        msp = doc.modelspace()

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
    except Exception as e:
        raise RuntimeError(f"Erreur dans image_to_dxf : {str(e)}")


        doc.saveas(output_file)
        return output_file
    except Exception as e:
        raise RuntimeError(f"Erreur lors de la conversion : {str(e)}")

@app.route('/convert', methods=['POST'])
def convert():
    """Route pour convertir une image PNG en DXF."""
    if 'file' not in request.files or 'color' not in request.form:
        return jsonify({"error": "Fichier ou couleur manquant"}), 400

    file = request.files['file']
    hex_color = request.form['color']  # Couleur au format #RRGGBB

    if file.filename == '':
        return jsonify({"error": "Aucun fichier sélectionné"}), 400

    try:
        # Convertir la couleur hexadécimale en RGB
        rgb_color = hex_to_rgb(hex_color)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    # Chemins pour les fichiers
    input_path = os.path.join(UPLOAD_FOLDER, file.filename)
    output_path = os.path.splitext(input_path)[0] + "_converted.dxf"

    # Sauvegarder l'image téléchargée
    file.save(input_path)

    # Convertir l'image
    try:
        image_to_dxf(input_path, output_path, rgb_color)
        return send_file(output_path, as_attachment=True, download_name="converted.dxf")
    except Exception as e:
        return jsonify({"error": f"Erreur lors de la conversion : {str(e)}"}), 500

if __name__ == "__main__":
    # Récupérer le port défini par Render ou utiliser 5000 par défaut
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
