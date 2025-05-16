import os
import json
import urllib.request
from pathlib import Path
from .utils import print_header

FLAVORS_DIR = "flavors"
IMAGES_DIR = "images"
DEFAULT_IMAGE_NAME = "ubuntu.img"
DEFAULT_IMAGE_PATH = os.path.join(IMAGES_DIR, DEFAULT_IMAGE_NAME)
IMAGE_URL = "https://cloud-images.ubuntu.com/minimal/releases/jammy/release/ubuntu-22.04-minimal-cloudimg-amd64.img"

def ensure_flavors_dir():
    os.makedirs(FLAVORS_DIR, exist_ok=True)

def ensure_images_dir():
    os.makedirs(IMAGES_DIR, exist_ok=True)

def ensure_default_image():
    ensure_images_dir()
    if not os.path.exists(DEFAULT_IMAGE_PATH):
        print(f"No se encontró {DEFAULT_IMAGE_NAME}. Descargando...")
        try:
            urllib.request.urlretrieve(IMAGE_URL, DEFAULT_IMAGE_PATH)
            print(f"Imagen descargada y guardada como {DEFAULT_IMAGE_PATH}")
        except Exception as e:
            print(f"Error al descargar la imagen: {e}")
            return False
    return True

def list_flavors():
    ensure_flavors_dir()
    flavor_files = list(Path(FLAVORS_DIR).glob("*.json"))
    return [f.stem for f in flavor_files]

def get_flavor_data(flavor_name):
    ensure_flavors_dir()
    flavor_path = os.path.join(FLAVORS_DIR, f"{flavor_name}.json")
    if not os.path.exists(flavor_path):
        return None
    try:
        with open(flavor_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error al cargar el flavor {flavor_name}: {e}")
        return None

def save_flavor(flavor_data):
    ensure_flavors_dir()
    flavor_name = flavor_data.get("name")
    if not flavor_name:
        print("Error: El flavor debe tener un nombre.")
        return False
    flavor_path = os.path.join(FLAVORS_DIR, f"{flavor_name}.json")
    try:
        with open(flavor_path, 'w') as f:
            json.dump(flavor_data, f, indent=2)
        return True
    except Exception as e:
        print(f"Error al guardar el flavor {flavor_name}: {e}")
        return False

def delete_flavor(flavor_name):
    ensure_flavors_dir()
    flavor_path = os.path.join(FLAVORS_DIR, f"{flavor_name}.json")
    if not os.path.exists(flavor_path):
        print(f"Error: El flavor {flavor_name} no existe.")
        return False
    try:
        os.remove(flavor_path)
        return True
    except Exception as e:
        print(f"Error al eliminar el flavor {flavor_name}: {e}")
        return False

def create_default_flavors():
    ensure_flavors_dir()
    ensure_default_image()
    default_flavors = [
        {"name": "tiny", "cpu": 1, "ram": 512, "disk": 1, "image": DEFAULT_IMAGE_NAME},
        {"name": "small", "cpu": 1, "ram": 1024, "disk": 10, "image": DEFAULT_IMAGE_NAME},
        {"name": "medium", "cpu": 2, "ram": 2048, "disk": 20, "image": DEFAULT_IMAGE_NAME},
        {"name": "large", "cpu": 4, "ram": 4096, "disk": 40, "image": DEFAULT_IMAGE_NAME}
    ]
    existing_flavors = list_flavors()
    for flavor in default_flavors:
        if flavor["name"] not in existing_flavors:
            save_flavor(flavor)
            print(f"Flavor predeterminado '{flavor['name']}' creado.")

def verify_flavor_exists():
    ensure_flavors_dir()
    if not list_flavors():
        print("No se encontraron flavors. Creando flavors predeterminados...")
        create_default_flavors()
    return len(list_flavors()) > 0

def select_flavor():
    if not verify_flavor_exists():
        print("Error: No hay flavors disponibles.")
        return None
    flavors = list_flavors()
    print("\nFlavors disponibles:")
    for i, flavor_name in enumerate(flavors):
        flavor_data = get_flavor_data(flavor_name)
        print(f"{i+1}. {flavor_name} (CPU: {flavor_data['cpu']}, RAM: {flavor_data['ram']}MB, Disk: {flavor_data['disk']}GB, Image: {flavor_data.get('image', 'N/A')})")
    try:
        selection = input("\nSeleccione un flavor (número) o presione Enter para crear uno nuevo: ")
        if not selection:
            return create_new_flavor()
        index = int(selection) - 1
        if 0 <= index < len(flavors):
            return flavors[index]
        else:
            print("Índice fuera de rango.")
            return select_flavor()
    except ValueError:
        print("Entrada inválida. Se espera un número entero.")
        return select_flavor()

def create_new_flavor():
    try:
        ensure_default_image()
        print("\nCreación de nuevo flavor:")
        name = input("Nombre del flavor: ")
        if not name:
            print("Operación cancelada.")
            return None
        if name in list_flavors():
            print(f"Ya existe un flavor con el nombre '{name}'.")
            overwrite = input("¿Desea sobrescribirlo? (s/n): ").lower() == 's'
            if not overwrite:
                return create_new_flavor()
        cpu = int(input("Número de CPUs (1-16): "))
        ram = int(input("RAM en MB (512-32768): "))
        disk = int(input("Disco en GB (1-1000): "))
        if cpu < 1 or cpu > 16 or ram < 512 or ram > 32768 or disk < 1 or disk > 1000:
            print("Valores fuera de rango. Intente de nuevo.")
            return create_new_flavor()
        image = DEFAULT_IMAGE_NAME
        flavor_data = {
            "name": name,
            "cpu": cpu,
            "ram": ram,
            "disk": disk,
            "image": image
        }
        if save_flavor(flavor_data):
            print(f"Flavor '{name}' creado con éxito.")
            return name
        else:
            print("Error al crear el flavor.")
            return select_flavor()
    except ValueError:
        print("Entrada inválida. Se espera un número entero.")
        return create_new_flavor()
    except KeyboardInterrupt:
        print("\nOperación cancelada.")
        return None

def manage_flavors():
    ensure_default_image()
    while True:
        print_header("Gestión de Flavors")

        #print("-----------------")
        print("1. Listar flavors existentes")
        print("2. Crear nuevo flavor")
        print("3. Modificar flavor existente")
        print("4. Eliminar flavor")
        print("5. Volver al menú anterior")
        try:
            option = int(input("\nSeleccione una opción (1-5): "))
            if option == 1:
                flavors = list_flavors()
                if not flavors:
                    print("No hay flavors definidos.")
                    verify_flavor_exists()
                else:
                    print_header("Flavors disponibles")
                    #print("\nFlavors disponibles:")
                    print("-" * 80)
                    print(f"{'Nombre':<15} {'CPU':<5} {'RAM (MB)':<10} {'Disco (GB)':<10} {'Imagen':<30}")
                    print("-" * 80)
                    for flavor_name in flavors:
                        flavor_data = get_flavor_data(flavor_name)
                        if flavor_data:
                            print(f"{flavor_name:<15} {flavor_data['cpu']:<5} {flavor_data['ram']:<10} {flavor_data['disk']:<10} {flavor_data.get('image', 'N/A'):<30}")
                    print("-" * 80)
                    input("\nPresione Enter para regresar al menú anteríor...")

            elif option == 2:
                create_new_flavor()
            elif option == 3:
                modify_flavor()
            elif option == 4:
                flavors = list_flavors()
                if not flavors:
                    print("No hay flavors para eliminar.")
                    continue
                print("\nSeleccione el flavor a eliminar:")
                for i, flavor_name in enumerate(flavors):
                    print(f"{i+1}. {flavor_name}")
                try:
                    index = int(input("\nFlavor a eliminar (número): ")) - 1
                    if 0 <= index < len(flavors):
                        flavor_name = flavors[index]
                        confirm = input(f"¿Está seguro de eliminar el flavor '{flavor_name}'? (s/n): ").lower() == 's'
                        if confirm:
                            if delete_flavor(flavor_name):
                                print(f"Flavor '{flavor_name}' eliminado con éxito.")
                            else:
                                print(f"Error al eliminar el flavor '{flavor_name}'.")
                        else:
                            print("Operación cancelada.")
                    else:
                        print("Índice fuera de rango.")
                except ValueError:
                    print("Entrada inválida. Se espera un número entero.")
            elif option == 5:
                break
            else:
                print("Opción inválida.")
        except ValueError:
            print("Entrada inválida. Se espera un número entero.")
        except KeyboardInterrupt:
            print("\nOperación cancelada.")
            return
def list_images():
    ensure_images_dir()
    images = [f for f in os.listdir(IMAGES_DIR) if os.path.isfile(os.path.join(IMAGES_DIR, f))]
    return images

def modify_flavor():
    flavors = list_flavors()
    if not flavors:
        print("No hay flavors para modificar.")
        return

    print("\nSeleccione el flavor a modificar:")
    for i, flavor_name in enumerate(flavors):
        print(f"{i+1}. {flavor_name}")
    try:
        index = int(input("Número de flavor a modificar: ")) - 1
        if index < 0 or index >= len(flavors):
            print("Índice fuera de rango.")
            return
        selected_flavor = flavors[index]
        flavor_data = get_flavor_data(selected_flavor)
        if not flavor_data:
            print("Error al cargar el flavor.")
            return

        print(f"\nModificando flavor '{selected_flavor}' (deje en blanco para mantener el valor actual):")

        name = input(f"Nuevo nombre [{flavor_data['name']}]: ") or flavor_data['name']
        cpu_input = input(f"Número de CPUs [{flavor_data['cpu']}]: ")
        ram_input = input(f"RAM en MB [{flavor_data['ram']}]: ")
        disk_input = input(f"Disco en GB [{flavor_data['disk']}]: ")

        images = list_images()
        if images:
            print("Imágenes disponibles:")
            for i, img in enumerate(images):
                print(f"{i+1}. {img}")
            image_input = input(f"Seleccione una imagen (1-{len(images)}) o Enter para mantener '{flavor_data.get('image', DEFAULT_IMAGE_NAME)}': ")
            if image_input.isdigit():
                image_index = int(image_input) - 1
                if 0 <= image_index < len(images):
                    image = images[image_index]
                else:
                    print("Índice fuera de rango, se mantendrá la imagen actual.")
                    image = flavor_data.get("image", DEFAULT_IMAGE_NAME)
            else:
                image = flavor_data.get("image", DEFAULT_IMAGE_NAME)
        else:
            print("No se encontraron imágenes disponibles. Se mantendrá la actual.")
            image = flavor_data.get("image", DEFAULT_IMAGE_NAME)

        cpu = int(cpu_input) if cpu_input else flavor_data['cpu']
        ram = int(ram_input) if ram_input else flavor_data['ram']
        disk = int(disk_input) if disk_input else flavor_data['disk']

        new_data = {
            "name": name,
            "cpu": cpu,
            "ram": ram,
            "disk": disk,
            "image": image
        }

        # Rename the file if name changed
        if name != selected_flavor:
            os.remove(os.path.join(FLAVORS_DIR, f"{selected_flavor}.json"))

        if save_flavor(new_data):
            print(f"Flavor '{name}' modificado con éxito.")
        else:
            print("Error al guardar el flavor modificado.")
    except ValueError:
        print("Entrada inválida.")
    except KeyboardInterrupt:
        print("\nOperación cancelada.")
