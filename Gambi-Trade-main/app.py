import os
from datetime import timedelta

from flask import (Flask, session, render_template, request, redirect,
                   url_for, flash)

from modelos import ActivoFinanciero, crear_desde_diccionario

app = Flask(__name__)

# Necesaria para que Flask pueda firmar la cookie de la session.
# En producción se define con la variable de entorno SECRET_KEY.
app.secret_key = os.environ.get("SECRET_KEY", "clave_de_desarrollo_cambiala")
# La sesión permanecerá durante 7 días
app.permanent_session_lifetime = timedelta(days=7)

# La session vive en una cookie (límite ~4 KB), así que limitamos las compras
MAX_ACTIVOS = 20


# ---------- Funciones auxiliares ----------

def obtener_activos():
    """Recupera los activos guardados en la sesión como objetos."""
    return [crear_desde_diccionario(datos) for datos in session.get("activos", [])]


def guardar_activos(lista_objetos):
    """Guarda la lista de objetos en la session.

    La session solo admite datos simples, así que se pasan a diccionarios.
    """
    session.permanent = True
    session["activos"] = [activo.a_diccionario() for activo in lista_objetos]


def buscar_activo(activos, id_activo):
    """Devuelve el activo con ese id, o None si no existe."""
    for activo in activos:
        if activo.get_id() == id_activo:
            return activo
    return None


def siguiente_id(activos):
    """Genera un id nuevo (máximo actual + 1) que no se repite al borrar."""
    return max((a.get_id() for a in activos), default=0) + 1


def numero_plano(valor):
    """Número sin ceros sobrantes ni notación científica: 0.50000000 -> 0.5"""
    texto = f"{valor:.8f}".rstrip("0").rstrip(".")
    return texto or "0"


def validar_formulario(formulario):
    """Valida los campos del formulario usando los setters del modelo.

    Devuelve (valores, errores): los textos escritos por el usuario y un
    diccionario con el mensaje de error de cada campo que falle.
    """
    valores = {
        "nombre": formulario.get("nombre", "").strip(),
        "simbolo": formulario.get("simbolo", "").strip(),
        "cantidad": formulario.get("cantidad", "").strip(),
        "precio": formulario.get("precio", "").strip(),
    }

    # Activo de prueba: solo sirve para reutilizar la validación de los setters
    prueba = ActivoFinanciero(0, "x", "x", 1, 1)
    setters = {
        "nombre": prueba.set_nombre,
        "simbolo": prueba.set_simbolo,
        "cantidad": prueba.set_cantidad,
        "precio": prueba.set_precio,
    }

    errores = {}
    for campo, setter in setters.items():
        try:
            setter(valores[campo])
        except ValueError as error:
            errores[campo] = str(error)

    return valores, errores


# ---------- Filtros para las plantillas ----------

@app.template_filter("euros")
def filtro_euros(valor):
    """1234.5 -> 1.234,50"""
    texto = f"{valor:,.2f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


@app.template_filter("cantidad")
def filtro_cantidad(valor):
    """0.5 -> 0,5"""
    return numero_plano(valor).replace(".", ",")


# ---------- Rutas ----------

@app.route("/")
def index():
    """Muestra la cartera con todas las compras y su valor total."""
    activos = obtener_activos()
    total = sum(activo.calcular_valor_total() for activo in activos)
    return render_template("index.html", activos=activos, total=total)


@app.route("/compras/nueva", methods=["GET", "POST"])
def nueva_compra():
    """Crear: muestra el formulario vacío (GET) y guarda la compra (POST)."""
    if request.method == "POST":
        activos = obtener_activos()

        if len(activos) >= MAX_ACTIVOS:
            flash(f"Has llegado al máximo de {MAX_ACTIVOS} compras. "
                  "Elimina alguna para añadir otra.", "error")
            return redirect(url_for("index"))

        valores, errores = validar_formulario(request.form)

        if not errores:
            nuevo = ActivoFinanciero(siguiente_id(activos), **valores)
            activos.append(nuevo)
            guardar_activos(activos)
            flash(f"Compra de {nuevo.get_nombre()} añadida.", "exito")
            return redirect(url_for("index"))

        return render_template("formulario.html", titulo="Nueva compra",
                               accion=url_for("nueva_compra"),
                               valores=valores, errores=errores)

    return render_template("formulario.html", titulo="Nueva compra",
                           accion=url_for("nueva_compra"),
                           valores={}, errores={})


@app.route("/activos/<int:id_activo>/editar", methods=["GET", "POST"])
def editar_activo(id_activo):
    """Editar: muestra el formulario con los datos actuales y guarda los cambios."""
    activos = obtener_activos()
    activo = buscar_activo(activos, id_activo)

    if activo is None:
        flash("Esa compra no existe.", "error")
        return redirect(url_for("index"))

    accion = url_for("editar_activo", id_activo=id_activo)

    if request.method == "POST":
        valores, errores = validar_formulario(request.form)

        if not errores:
            activo.set_nombre(valores["nombre"])
            activo.set_simbolo(valores["simbolo"])
            activo.set_cantidad(valores["cantidad"])
            activo.set_precio(valores["precio"])
            guardar_activos(activos)
            flash(f"Compra de {activo.get_nombre()} actualizada.", "exito")
            return redirect(url_for("index"))

        return render_template("formulario.html", titulo="Editar compra",
                               accion=accion, valores=valores, errores=errores)

    valores = {
        "nombre": activo.get_nombre(),
        "simbolo": activo.get_simbolo(),
        "cantidad": filtro_cantidad(activo.get_cantidad()),
        "precio": filtro_cantidad(activo.get_precio()),
    }
    return render_template("formulario.html", titulo="Editar compra",
                           accion=accion, valores=valores, errores={})


@app.route("/activos/<int:id_activo>/eliminar", methods=["POST"])
def eliminar_activo(id_activo):
    """Eliminar: solo por POST, para que un enlace no pueda borrar datos."""
    activos = obtener_activos()
    activo = buscar_activo(activos, id_activo)

    if activo is None:
        flash("Esa compra no existe.", "error")
    else:
        activos.remove(activo)
        guardar_activos(activos)
        flash(f"Compra de {activo.get_nombre()} eliminada.", "exito")

    return redirect(url_for("index"))


@app.errorhandler(404)
def pagina_no_encontrada(error):
    flash("No hemos encontrado esa página.", "error")
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
