from django.core.management.base import BaseCommand
from inventario.models import MarcaVehiculo, ModeloVehiculo, TipoVehiculo
import random
import string

class Command(BaseCommand):
    help = 'Cargar marcas, tipo de vehiculo y modelos de vehículos de prueba'

    def handle(self, *args, **kwargs):

        # Cargar marcas de vehículos
        marcas = [
            ("Hyundai", "Marca sud-coreana de vehículos"),
            ("Kia", "Marca sud-coreana de vehículos"),
            ("Genesis", "Marca sud-coreana de vehículos de lujo"),
            ("KG Mobility", "Marca sud-coreana de vehículos comerciales, SsangYong rebrandeada"),
            ("Renault Korea Motors", "Marca coreana de vehículos")
        ]

        for marca_name, descripcion in marcas:
            MarcaVehiculo.objects.get_or_create(nombre=marca_name, descripcion=descripcion)
        
        # cargar tipos de vehículos 
        tipos_vehiculo = [
            ("Hatchback", "Vehículos compactos sin maletero separado, con una puerta trasera que se abre hacia arriba"),
            ("Sedán", "Vehículo con maletero separado y tres volúmenes definidos"),
            ("Coupé", "Vehículo de dos puertas con línea de techo baja"),
            ("Convertible", "Vehículo con techo retráctil o removible"),
            ("SUV", "Vehículo con mayor altura al suelo"),
            ("Crossover", "Vehículo basado en plataformas de automóviles pero con estética de SUV"),
            ("Minivan", "Vehículo diseñado para maximizar el espacio interior"),
            ("Pickup", "Vehículo con cabina cerrada y caja de carga abierta"),
            ("Furgón", "Vehículo cerrado diseñado para transporte de carga"), 
                ("MPV", "Vehículo multipropósito, similar a una minivan pero con un enfoque más versátil"),
                ("Eléctrico", "Vehículo propulsado exclusivamente por energía eléctrica"),
                ("Híbrido", "Vehículo que combina un motor de combustión interna con uno o más motores eléctricos"),
                ("Todoterreno", "Vehículo diseñado para manejar terrenos difíciles, generalmente con tracción en las cuatro ruedas")
        ]

        for tipo_name, descripcion in tipos_vehiculo:
            TipoVehiculo.objects.get_or_create(nombre=tipo_name, descripcion=descripcion)

        # Cargar modelos de vehículos
        modelos = [
            ("Hyundai", (("Grand i10", "Hatchback", "Hatchback y Sedán subcompacto, ideal para uso urbano por su economía de combustible."),
                        ("Grand i10", "Sedán", "Hatchback y Sedán subcompacto, ideal para uso urbano por su economía de combustible."),
                        ("Accent / Verna", "Sedán", "Un sedán compacto clásico, muy popular por su durabilidad y mantenimiento sencillo."),
                        ("Elantra / Avante", "Sedán", "Sedán mediano con un diseño muy marcado y tecnológico."),
                        ("Sonata", "Sedán", "Sedán de tamaño mediano/grande, enfocado en el confort y un perfil más ejecutivo."),
                        ("Venue", "SUV", "El SUV de entrada, compacto y eficiente para ciudad."),
                        ("Kona", "Crossover", "Crossover con un diseño atrevido; disponible en versiones a combustión, híbrida y eléctrica."),
                        ("Creta", "SUV", "Uno de los SUVs más vendidos en la región, excelente equilibrio entre tamaño y funcionalidad."),
                        ("Tucson", "SUV", "El SUV insignia de tamaño mediano, conocido por su versatilidad familiar y tecnología de seguridad."),
                        ("Santa Fe", "SUV", "SUV mediano/grande, con capacidad para 7 pasajeros en muchas configuraciones."),
                        ("Palisade", "SUV", "El SUV más grande y lujoso de la marca, enfocado en el máximo confort para toda la familia."),
                        ("IONIQ 5", "SUV", "SUV eléctrico con diseño retro-futurista y carga ultrarrápida."),
                        ("IONIQ 6", "Sedán", "Sedán eléctrico aerodinámico diseñado para máxima eficiencia y autonomía."),
                        ("Staria", "Furgón", "Minivan/Furgón futurista que reemplazó a la antigua H1, ideal para transporte ejecutivo o de carga."),
                        ("H100", "Pickup", "El camión ligero de carga por excelencia para el trabajo pesado en logística urbana."))),
            ("Kia", (("Picanto", "Hatchback", "Un icónico city-car (hatchback) extremadamente popular por su tamaño compacto y maniobrabilidad."),
                        ("Rio", "Sedán", "Sedán o hatchback compacto (aunque en algunos mercados está siendo reemplazado por modelos de mayor tamaño)."),
                        ("K3", "Sedán", "Sedán compacto moderno que ha reemplazado a varios modelos anteriores en la gama de Kia, destacando por su tecnología y diseño."),
                        ("Cerato / Forte", "Sedán", "Sedán mediano de corte deportivo y familiar."),
                        ("K5 / Optima", "Sedán", "Sedán mediano de diseño muy estilizado, enfocado en confort y rendimiento."),
                        ("Sonet", "SUV", "SUV subcompacto diseñado principalmente para mercados emergentes, muy popular por su equipamiento."),
                        ("Seltos", "SUV", "SUV compacto que ofrece un gran equilibrio entre tamaño, diseño y funcionalidad."),
                        ("Sportage", "SUV", "El SUV mediano por excelencia de la marca. Es uno de sus vehículos más vendidos a nivel mundial."),
                        ("Sorento", "SUV", "SUV de tres filas de asientos, enfocado en familias que buscan mayor espacio y acabados superiores."),
                        ("Telluride", "SUV", "El SUV más grande y robusto de Kia, enfocado principalmente en mercados como Norteamérica, con capacidad para hasta 8 pasajeros."),
                        ("Carnival", "Minivan", "Es la referencia en el mercado de minivans/MPVs. Kia la denomina 'Vehículo Utilitario Multipropósito', ofreciendo un espacio interior que compite con vehículos de gama alta."),
                        ("EV6", "Crossover Eléctrico", "Crossover eléctrico con un diseño vanguardista y capacidades de carga ultrarrápida."),
                        ("EV9", "SUV Eléctrico", "SUV grande totalmente eléctrico con tres filas de asientos, que marca el nuevo estándar tecnológico de la marca."))),
            ("Genesis", (("G70", "Sedán Deportivo", "Sedán deportivo compacto que compite directamente con modelos como el BMW Serie 3 o el Audi A4. Se caracteriza por su agilidad y estilo dinámico."),
                        ("G80", "Sedán Ejecutivo", "El sedán ejecutivo mediano de la marca, conocido por su equilibrio perfecto entre lujo, confort de marcha y diseño sofisticado."),
                        ("G90", "Sedán de Representación", "El modelo insignia de la marca. Es un sedán de representación de gran tamaño, diseñado para competir contra el Mercedes-Benz Clase S, enfocado en el máximo lujo y confort para los pasajeros traseros."),
                        ("GV60", "Crossover", "Un crossover 100 porciento eléctrico con un diseño muy distintivo y tecnológico, basado en la plataforma eléctrica global del grupo."),
                        ("GV70", "SUV", "Un SUV compacto/mediano de estilo deportivo que ha tenido un gran éxito por su diseño llamativo y su interior de alta calidad."),
                        ("GV80", "SUV", "El SUV grande de la marca. Ofrece una presencia imponente, mucho espacio interior y un nivel de acabados que lo sitúa en lo más alto del segmento premium."),
                        ("Electrified G80", "Sedán", "La versión eléctrica del G80."),
                        ("Electrified GV70", "SUV", "La versión eléctrica del SUV mediano."))),
            ("KG Mobility", (("Tivoli", "SUV", "Un SUV compacto (crossover) orientado al uso urbano, conocido por ser uno de los modelos más accesibles y personalizables de la marca."),
                            ("Korando", "SUV", "Es el SUV mediano de la firma. Históricamente uno de sus modelos con mayor trayectoria, equilibrando capacidad de carga y manejo en ciudad."),
                            ("Torres", "SUV", "Este modelo representa la nueva era de la marca bajo el nombre KG Mobility. Tiene un diseño de estilo 'off-road' retro-futurista, muy robusto y con gran capacidad de espacio."),
                            ("Rexton", "SUV", "Es el buque insignia en cuanto a capacidad todoterreno. Es un SUV de chasis de largueros (tradicional 4x4), diseñado para trabajo pesado, arrastre y terrenos difíciles."),
                            ("Musso / Rexton Sports", "Pickup", "Es la camioneta (pickup) de la marca. Comparte plataforma con el Rexton, ofreciendo una gran capacidad de carga y tracción integral, muy valorada para entornos rurales o de construcción."),
                            ("Torres EVX", "SUV", "La versión 100 porciento eléctrica del popular modelo Torres. Mantiene el diseño robusto pero con una configuración motriz de cero emisiones."),
                            ("KGM Korando e-Motion", "SUV", "La variante eléctrica del Korando, adaptada para mantener la funcionalidad familiar con una motorización sustentable."))),
            ("Renault Korea Motors", (("SM3", "Sedán", "Sedán compacto basado en el Renault Fluence, conocido por su eficiencia y confort."),
                                    ("SM5", "Sedán", "Sedán mediano que ofrece un buen equilibrio entre espacio interior y rendimiento."),
                                    ("SM6", "Sedán", "Sedán de tamaño mediano/grande con un diseño más moderno y tecnología avanzada."),
                                    ("QM3 / Captur", "SUV", "SUV compacto basado en el Renault Captur, ideal para la ciudad."),
                                    ("QM5 / Koleos", "SUV", "SUV mediano que combina estilo europeo con funcionalidad."),
                                    ("QM6 / Koleos", "SUV", "SUV de tamaño mediano/grande con un enfoque en el confort y la tecnología.")))   
            ]
        


        for marca_name, modelo_data in modelos:
            marca = MarcaVehiculo.objects.get(nombre=marca_name)
            for modelo_name, tipo_name, descripcion in modelo_data:
                tipo, _ = TipoVehiculo.objects.get_or_create(
                    nombre=tipo_name,
                    defaults={'descripcion': ''}
                )
                ModeloVehiculo.objects.get_or_create(
                    nombre=modelo_name,
                    marca=marca,
                    tipo_vehiculo=tipo,
                    descripcion=descripcion
                )
        self.stdout.write(self.style.SUCCESS('Marcas, tipos de vehículos y modelos cargados exitosamente.'))
