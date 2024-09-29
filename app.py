from flask import Flask, render_template, request
from flask_wtf import FlaskForm
from wtforms import FileField, SubmitField, SelectField
from werkzeug.utils import secure_filename
import os
from wtforms.validators import InputRequired
import pandas as pd

app = Flask(__name__)
app.config['SECRET_KEY'] = 'supersecretkey'
app.config['UPLOAD_FOLDER'] = 'static/files'

class UploadFileForm(FlaskForm):
    file = FileField("File", validators=[InputRequired()])
    professional = SelectField('Escolha o Profissional', choices=[('Nutricionista'), ('Dr. Guilherme Braz')], validators=[InputRequired()])
    submit = SubmitField("Upload File")

@app.route('/', methods=['GET', 'POST'])
@app.route('/home', methods=['GET', 'POST'])
def home():
    form = UploadFileForm()
    
    # Criar a pasta de upload caso não exista
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

    if form.validate_on_submit():
        file = form.file.data
        filename = secure_filename(file.filename)
        file_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        # Lendo o arquivo Excel
        df = pd.read_excel(file_path, skiprows=2)
        df.columns = ['Horario', 'Paciente', 'Primeira_consulta', 'Status', 'Consulta_retorno', 'Plano_saude', 'Tipo_consulta', 'Compromisso', 'Procedimento']
        mensagens = []

        # Obter a data da consulta
        data_consulta = pd.read_excel(file_path, skiprows=0).iloc[0, 0]

        # Função para simplificar e formatar múltiplos procedimentos
        def simplificar_procedimentos(procedimento):
            # Verificar se procedimento é um valor válido
            if not isinstance(procedimento, str):
                return procedimento  # ou return '' para retornar uma string vazia

            # Substituir procedimentos longos por suas versões curtas
            procedimento = procedimento.replace('Endoscopia digestiva alta', 'Endoscopia')
            procedimento = procedimento.replace('Colonoscopia com biópsia e/ou citologia', 'Colonoscopia')
            procedimento = procedimento.replace('Consulta em consultório (no horário normal ou preestabelecido)', 'Consulta')

            # Se houver múltiplos procedimentos, ajustar o formato
            procedimentos = [p.strip() for p in procedimento.split(',')]
            if len(procedimentos) > 1:
                # Se for o último procedimento, usa "e" ao invés de vírgula
                return ', '.join(procedimentos[:-1]) + ' e ' + procedimentos[-1]
            return procedimento


        # Função para gerar a mensagem
        def gerar_mensagem(paciente, data_consulta, horario_consulta, procedimento):
            if pd.isna(horario_consulta):
                return None

            # Simplificar o procedimento e formatar para múltiplos casos
            procedimento_simplificado = simplificar_procedimentos(procedimento)
            profissional = form.professional.data  # Obtém a opção selecionada

            return (
                f"Olá, {paciente}!\n"  # Quebra de linha após a saudação
                f"Gostaria de confirmar {procedimento_simplificado} com {profissional} na Clínica Braz.\n"  # Quebra de linha após o procedimento
                f"Data: {data_consulta}\n"  # Quebra de linha após a data
                f"Horário: {horario_consulta}\n"  # Quebra de linha após o horário
                "Por favor, digite (c) para confirmar ou (n) para desmarcar/remarcar."
            )


        # Gerar mensagens
        for index, row in df.iterrows():
            paciente = row['Paciente']
            horario_consulta = row['Horario']
            procedimento = row['Procedimento']

            if pd.notna(paciente) and pd.notna(horario_consulta):
                mensagem = gerar_mensagem(paciente, data_consulta, horario_consulta, procedimento)
                if mensagem:
                    mensagens.append(mensagem)
                    print(f"Enviando para {paciente}: {mensagem}")

        os.remove(file_path)

        return render_template('confirmation.html', messages=mensagens)

    return render_template('index.html', form=form)

if __name__ == '__main__':
    app.run()
