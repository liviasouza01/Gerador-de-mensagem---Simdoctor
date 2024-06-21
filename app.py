from flask import Flask, render_template, request
from flask_wtf import FlaskForm
from wtforms import FileField, SubmitField
from werkzeug.utils import secure_filename
import os
from wtforms.validators import InputRequired
import pandas as pd

app = Flask(__name__)
app.config['SECRET_KEY'] = 'supersecretkey'
app.config['UPLOAD_FOLDER'] = 'static/files'

class UploadFileForm(FlaskForm):
    file = FileField("File", validators=[InputRequired()])
    submit = SubmitField("Upload File")

@app.route('/', methods=['GET', 'POST'])
@app.route('/home', methods=['GET', 'POST'])
def home():
    form = UploadFileForm()
    if form.validate_on_submit():
        file = form.file.data  # First grab the file
        filename = secure_filename(file.filename)
        file_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)  # Then save the file

        # Read the Excel file and extract necessary information
        df = pd.read_excel(file_path, skiprows=2)
        df.columns = ['Horario', 'Paciente', 'Primeira_consulta', 'Status', 'Consulta_retorno', 'Plano_saude', 'Tipo_consulta', 'Compromisso', 'Procedimento']
        mensagens = []

        # Extract the date from the second row of the original file
        data_consulta = pd.read_excel(file_path, skiprows=0).iloc[0, 0]

        def gerar_mensagem(paciente, data_consulta, horario_consulta, status):
            if pd.isna(horario_consulta):
                return None
            return f"Olá {paciente}, gostaria de confirmar sua consulta do dia {data_consulta} às {horario_consulta} na Clínica Braz. Por favor, digite (c) para confirmado ou (n) para desmarcar/remarcar."

        for index, row in df.iterrows():
            paciente = row['Paciente']
            horario_consulta = row['Horario']
            status = row['Status']

            if pd.notna(paciente) and pd.notna(horario_consulta):
                mensagem = gerar_mensagem(paciente, data_consulta, horario_consulta, status)
                if mensagem:
                    mensagens.append(mensagem)
                    # Opcional: Exibir a mensagem no console
                    print(f"Enviando para {paciente}: {mensagem}")

        return render_template('confirmation.html', messages=mensagens)

    return render_template('index.html', form=form)

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(host='0.0.0.0', port=8080)
