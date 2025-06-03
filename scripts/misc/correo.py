import smtplib
from email.mime.text import MIMEText
import sys

def enviar_correo(nombre, apellido, destinatario):
    remitente = "nanpicorreos@gmail.com"
    copia = "jbzambrano@pucp.pe"
    contraseña = "bczj fahq fyqb xojw"  # Reemplaza con tu contraseña de aplicación de Gmail 

    # Cuerpo del correo (asegurar que se usa UTF-8)
    mensaje = f"""\
    ¡Buenos días!

    Mi nombre es {nombre} {apellido} y estoy muy feliz de llevar este curso ;)
    Prometo ir a los laboratorios con un buen avance para poder aprovechar el curso.

    Atte. {nombre} {apellido}
    """

    # Configuración del correo (asegurar UTF-8)
    msg = MIMEText(mensaje, "plain", "utf-8")
    msg["Subject"] = "Saludos desde Python"
    msg["From"] = remitente
    msg["To"] = destinatario
    msg["Cc"] = copia

    # Configuración del servidor SMTP
    try:
        servidor = smtplib.SMTP("smtp.gmail.com", 587)
        servidor.starttls()
        servidor.login(remitente, contraseña)  # Usa la contraseña de aplicación
        servidor.sendmail(remitente, [destinatario, copia], msg.as_string().encode("utf-8"))  # Asegurar UTF-8
        servidor.quit()
        print("Correo enviado correctamente.")
    except Exception as e:
        print("Error al enviar el correo:", e)

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Uso: python script.py <Nombre> <Apellido> <CorreoDestinatario>")
    else:
        # Asegurar que los argumentos estén en UTF-8
        nombre = sys.argv[1].encode("utf-8").decode("utf-8")
        apellido = sys.argv[2].encode("utf-8").decode("utf-8")
        destinatario = sys.argv[3]

        enviar_correo(nombre, apellido, destinatario)
