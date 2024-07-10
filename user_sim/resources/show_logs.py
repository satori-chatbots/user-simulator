import logging

# class get_logs:
#
#     def __init__(self, show=False):
#
#         self.show_l = show
#         self.logger = self.config_logger()
#
#         if self.show_l:
#             # Crear un manejador para escribir en archivo
#             file_handler = logging.FileHandler('app.log')
#             file_handler.setLevel(logging.DEBUG)  # Configurar el nivel de log para el archivo
#
#             # Crear un manejador para mostrar en la consola
#             console_handler = logging.StreamHandler()
#             console_handler.setLevel(logging.DEBUG)  # Configurar el nivel de log para la consola
#
#             # Crear un formato y asignarlo a los manejadores
#             formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
#             file_handler.setFormatter(formatter)
#             console_handler.setFormatter(formatter)
#
#             # Agregar los manejadores al logger
#             self.logger.addHandler(file_handler)
#             self.logger.addHandler(console_handler)
#         else:
#             # Si no se muestran los logs, se puede agregar un manejador que no haga nada
#             self.logger.addHandler(logging.NullHandler())
#
#
#     def config_logger(self):
#         # Configurar el logger
#         logger = logging.getLogger('mi_logger')
#         logger.setLevel(logging.DEBUG)  # Configurar el nivel de log
#
#         return logger

import logging

class LoggerConfig:
    def __init__(self, mostrar_logs=True):
        self.mostrar_logs = mostrar_logs
        self.configure_logger()

    def configure_logger(self):
        logger = logging.getLogger('mi_logger')
        logger.setLevel(logging.DEBUG)

        # Verificar si ya se han agregado manejadores para evitar duplicados
        if not logger.hasHandlers():
            if self.mostrar_logs:
                file_handler = logging.FileHandler('../../app.log')
                file_handler.setLevel(logging.DEBUG)

                console_handler = logging.StreamHandler()
                console_handler.setLevel(logging.DEBUG)

                formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
                file_handler.setFormatter(formatter)
                console_handler.setFormatter(formatter)

                logger.addHandler(file_handler)
                logger.addHandler(console_handler)
            else:
                logger.addHandler(logging.NullHandler())

# Instanciar la configuración del logger
logger_config = LoggerConfig(mostrar_logs=True)

# Obtener el logger configurado
logger = logging.getLogger('my_logger')



# # Variable para controlar el logging
# mostrar_logs = True
#
# # Configurar el logger
# logger = logging.getLogger('mi_logger')
# logger.setLevel(logging.DEBUG)  # Configurar el nivel de log
#
# if mostrar_logs:
#     # Crear un manejador para escribir en archivo
#     file_handler = logging.FileHandler('app.log')
#     file_handler.setLevel(logging.DEBUG)  # Configurar el nivel de log para el archivo
#
#     # Crear un manejador para mostrar en la consola
#     console_handler = logging.StreamHandler()
#     console_handler.setLevel(logging.DEBUG)  # Configurar el nivel de log para la consola
#
#     # Crear un formato y asignarlo a los manejadores
#     formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
#     file_handler.setFormatter(formatter)
#     console_handler.setFormatter(formatter)
#
#     # Agregar los manejadores al logger
#     logger.addHandler(file_handler)
#     logger.addHandler(console_handler)
# else:
#     # Si no se muestran los logs, se puede agregar un manejador que no haga nada
#     logger.addHandler(logging.NullHandler())

# Ejemplo de código con una condición if
# valor = 10
#
# my_logs = show_logs(True)
#
#
# if valor > 5:
#     my_logs.logger.info(f"El valor es mayor que 5: {valor}")
#
# # Más lógica del programa
