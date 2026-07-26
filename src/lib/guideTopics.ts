export interface GuideLink {
  label: string;
  url: string;
}

export interface GuideRow {
  term: string;
  description: string;
}

export interface GuideTopic {
  id: string;
  section: string;
  label: string;
  title: string;
  summary: string;
  paragraphs: string[];
  rows?: GuideRow[];
  callout?: string;
  links?: GuideLink[];
}

export const GUIDE_TOPICS: GuideTopic[] = [
  {
    id: 'vision', section: 'Orientación', label: '1 · Qué estás viendo', title: 'La tabla como mapa científico',
    summary: 'Cómo se relacionan la cuadrícula, el zoom progresivo y la ficha maestra.',
    paragraphs: [
      'TablaElementos no presenta una simple lista de símbolos. La posición de cada casilla resume el número de capas ocupadas, el tipo de subnivel electrónico que se está llenando y semejanzas químicas con los elementos vecinos.',
      'La vista general prioriza identidad y posición. Al ampliar se incorporan propiedades seleccionadas y, al abrir una casilla, la ficha maestra separa los dominios que necesitan definiciones, condiciones y visualizaciones diferentes.',
      'Que una pestaña exista no significa que todos sus campos estén disponibles para todos los elementos. La interfaz distingue entre dato medido, evaluado, calculado, derivado, no aplicable y todavía no incorporado.'
    ],
    rows: [
      { term: 'Tabla', description: 'Mapa periódico de los 118 elementos en disposición corta o larga.' },
      { term: 'Casilla', description: 'Resumen progresivo que gana información al aumentar el zoom.' },
      { term: 'Ficha maestra', description: 'Espacio documental con electrónica, materiales, núcleo, espectros, termodinámica, radiación y contexto.' },
      { term: 'Guía contextual', description: 'Los botones de información de cada pestaña abren directamente el capítulo relacionado.' }
    ],
    callout: 'Una ausencia de datos no debe leerse como cero. Puede significar que la magnitud no aplica, no se ha evaluado o todavía no se ha importado.',
    links: [
      { label: 'IUPAC · Periodic Table', url: 'https://iupac.org/what-we-do/periodic-table-of-elements/' },
      { label: 'PubChem · Periodic Table', url: 'https://pubchem.ncbi.nlm.nih.gov/periodic-table/' }
    ]
  },
  {
    id: 'anatomia', section: 'Orientación', label: '2 · Anatomía de la casilla', title: 'Cómo leer una casilla progresiva',
    summary: 'Qué aparece en cada nivel de ampliación y por qué no se muestra todo a la vez.',
    paragraphs: [
      'La casilla mínima contiene número atómico, símbolo y nombre. Los siguientes niveles añaden masa y estado estándar, después configuración, electronegatividad, radio y densidad, y finalmente energías y posición periódica.',
      'El contenido se distribuye alrededor del símbolo para conservar una referencia visual estable. La ficha no cambia de posición al aparecer nuevos datos; solo cambia el nivel informativo.',
      'Los valores compactos son accesos rápidos. La interpretación rigurosa, la fuente y las condiciones se consultan en la ficha maestra.'
    ],
    rows: [
      { term: 'Esquina superior', description: 'Número atómico Z.' },
      { term: 'Centro', description: 'Símbolo químico y nombre.' },
      { term: 'Perímetro', description: 'Propiedades resumidas que aparecen según el nivel de zoom.' },
      { term: 'Color', description: 'Familia química; no representa automáticamente una propiedad numérica.' }
    ]
  },
  {
    id: 'identidad', section: 'Orientación', label: '3 · Identidad y posición', title: 'Nombre, símbolo y número atómico',
    summary: 'Las magnitudes que identifican inequívocamente un elemento.',
    paragraphs: [
      'El número atómico Z es el número de protones del núcleo y define el elemento. Un átomo neutro posee también Z electrones, pero un ion puede tener más o menos electrones sin dejar de ser el mismo elemento.',
      'El símbolo es la abreviatura internacional. Algunos símbolos conservan raíces históricas o latinas, como Fe, Na, K y W. El nombre mostrado por la interfaz es la variante española, mientras que la estructura de carpetas conserva también el nombre inglés.',
      'Grupo, periodo y bloque describen la ubicación periódica, no la identidad. Dos isótopos comparten Z y símbolo aunque tengan distinto número de neutrones.'
    ],
    rows: [
      { term: 'Z', description: 'Cantidad de protones y posición ordinal en la tabla.' },
      { term: 'Símbolo', description: 'Abreviatura normalizada de una a tres letras.' },
      { term: 'Nombre', description: 'Denominación lingüística oficial o histórica.' },
      { term: 'A', description: 'Número másico de un nucleído concreto; no identifica por sí solo al elemento.' }
    ]
  },
  {
    id: 'organizacion', section: 'Orientación', label: '4 · Grupo, periodo y bloque', title: 'La arquitectura de la tabla periódica',
    summary: 'Por qué los elementos ocupan una fila, una columna y un bloque determinados.',
    paragraphs: [
      'Los periodos son filas relacionadas con el llenado de niveles principales. Los grupos son columnas que reúnen patrones de valencia y comportamiento, aunque las semejanzas no son idénticas en todos los miembros.',
      'Los bloques s, p, d y f indican el tipo de subnivel que recibe el electrón diferenciador. El helio se coloca con los gases nobles por su comportamiento aunque su configuración pertenezca al bloque s.',
      'La vista corta separa lantánidos y actínidos para ahorrar anchura. La vista larga abre el hueco central e integra el bloque f en los periodos 6 y 7.'
    ],
    rows: [
      { term: 'Bloque s', description: 'Grupos 1 y 2, además del helio por configuración.' },
      { term: 'Bloque p', description: 'Grupos 13 a 18.' },
      { term: 'Bloque d', description: 'Metales de transición.' },
      { term: 'Bloque f', description: 'Lantánidos y actínidos.' }
    ]
  },
  {
    id: 'familias', section: 'Orientación', label: '5 · Familias químicas', title: 'Categorías, familias y fronteras convencionales',
    summary: 'Cómo interpretar alcalinos, halógenos, gases nobles, metaloides y otras clases.',
    paragraphs: [
      'Las familias resumen semejanzas útiles de configuración y reactividad. Los alcalinos suelen formar cationes +1, los halógenos aniones −1 y los gases nobles presentan capas cerradas o casi cerradas.',
      'Las fronteras de categorías como metaloide o metal postransición varían entre fuentes. La tabla conserva una clasificación coherente para colorear y filtrar, pero no la presenta como una ley física absoluta.',
      'En lantánidos y actínidos, la química está condicionada por orbitales f y por una gran cantidad de estados electrónicos cercanos.'
    ],
    rows: [
      { term: 'Alcalinos', description: 'Grupo 1 salvo hidrógeno; metales muy reactivos.' },
      { term: 'Alcalinotérreos', description: 'Grupo 2; tendencia habitual a +2.' },
      { term: 'Halógenos', description: 'Grupo 17; gran afinidad por electrones en muchos contextos.' },
      { term: 'Gases nobles', description: 'Grupo 18; baja reactividad ordinaria, no inercia absoluta.' },
      { term: 'Metaloides', description: 'Categoría convencional con propiedades intermedias o semiconductoras.' }
    ]
  },
  {
    id: 'masa', section: 'Átomo y electrones', label: '6 · Masa y peso atómico', title: 'Masa isotópica, número másico y peso estándar',
    summary: 'Por qué aparecen números enteros, decimales e intervalos para la masa.',
    paragraphs: [
      'La masa isotópica corresponde a un nucleído concreto. El número másico A es el entero Z + N. El peso atómico estándar es un promedio ponderado que depende de la composición isotópica natural.',
      'CIAAW puede publicar un intervalo cuando la composición isotópica terrestre varía entre materiales normales. Ese intervalo expresa variación natural real, no un error de la tabla.',
      'Para elementos sin composición isotópica natural característica suele mostrarse entre corchetes el número másico de un isótopo representativo en tablas convencionales.'
    ],
    rows: [
      { term: 'u', description: 'Unidad de masa atómica unificada.' },
      { term: 'A', description: 'Número entero de protones más neutrones.' },
      { term: 'Masa isotópica', description: 'Masa de un nucleído concreto.' },
      { term: 'Peso estándar', description: 'Promedio recomendado para materiales terrestres normales.' }
    ],
    links: [{ label: 'CIAAW · Atomic Weights', url: 'https://ciaaw.org/atomic-weights.htm' }]
  },
  {
    id: 'atom-model', section: 'Átomo y electrones', label: '7 · Átomo 3D', title: 'Qué representa el modelo atómico tridimensional',
    summary: 'Alcance y límites del simulador visual de núcleo, capas y electrones.',
    paragraphs: [
      'El modelo 3D es una representación didáctica: ayuda a contar protones, neutrones estimados, electrones y capas ocupadas. Las trayectorias visibles no son órbitas planetarias reales.',
      'En mecánica cuántica, los electrones se describen mediante estados y distribuciones de probabilidad. El tamaño del núcleo y las distancias electrónicas tampoco están representados a la misma escala.',
      'La animación puede pausarse para inspeccionar el reparto por capas. Para estudiar orbitales, términos y energías debe utilizarse la pestaña Electrones o Niveles.'
    ],
    rows: [
      { term: 'Protones', description: 'Determinan Z y la identidad química.' },
      { term: 'Neutrones', description: 'Cambian entre isótopos.' },
      { term: 'Electrones', description: 'Z en el átomo neutro; cambian al formar iones.' },
      { term: 'Capas', description: 'Agrupación por número cuántico principal n.' }
    ],
    callout: 'La visualización es educativa y no pretende reproducir tamaños, velocidades ni trayectorias cuánticas literales.'
  },
  {
    id: 'configuration', section: 'Átomo y electrones', label: '8 · Configuración electrónica', title: 'Capas, subniveles y orbitales',
    summary: 'Cómo leer notaciones como [Ar] 3d⁶ 4s².',
    paragraphs: [
      'La configuración electrónica distribuye los electrones entre orbitales s, p, d y f. El superíndice indica cuántos electrones ocupan un subnivel.',
      'La configuración abreviada sustituye las capas internas por el símbolo del gas noble anterior. Las configuraciones publicadas suelen corresponder al estado fundamental del átomo neutro aislado.',
      'Aufbau, Hund y Pauli explican el patrón general, pero existen excepciones cuando varios subniveles tienen energías muy cercanas.'
    ],
    rows: [
      { term: 'n', description: 'Nivel principal: 1, 2, 3…' },
      { term: 's, p, d, f', description: 'Subniveles con capacidades 2, 6, 10 y 14.' },
      { term: 'Estado fundamental', description: 'Configuración de menor energía del sistema aislado.' },
      { term: 'Configuración abreviada', description: 'Núcleo de gas noble más electrones externos.' }
    ]
  },
  {
    id: 'valence', section: 'Átomo y electrones', label: '9 · Valencia y electrones', title: 'Valencia, electrones de valencia y oxidación',
    summary: 'Tres conceptos relacionados que no deben tratarse como sinónimos.',
    paragraphs: [
      'Los electrones de valencia son los que participan con mayor frecuencia en enlaces y reactividad. En los bloques s y p suelen coincidir con los electrones de la capa exterior; en transición y bloque f la definición depende del criterio químico.',
      'La valencia describe capacidad de combinación. Los estados de oxidación son cargas formales asignadas mediante reglas de contabilidad electrónica. Un mismo elemento puede presentar varias valencias y estados de oxidación.',
      'La pestaña Electrones separa configuración de valencia, electrones exteriores, electrones de valencia, valencias comunes y estados de oxidación para evitar una simplificación engañosa.'
    ],
    rows: [
      { term: 'Capa exterior', description: 'Electrones con el mayor n ocupado.' },
      { term: 'Electrones de valencia', description: 'Electrones disponibles para enlace según el contexto químico.' },
      { term: 'Valencia', description: 'Capacidad de combinación expresada mediante enlaces o equivalentes monovalentes.' },
      { term: 'Estado de oxidación', description: 'Carga formal de un átomo dentro de una especie química.' },
      { term: 'Bloque d/f', description: 'Puede requerir contar orbitales de más de una capa.' }
    ],
    callout: 'En metales de transición no existe siempre un único número universal de electrones de valencia.'
  },
  {
    id: 'electronegativity', section: 'Átomo y electrones', label: '10 · Electronegatividad', title: 'Atracción de densidad electrónica',
    summary: 'Qué significa la escala de Pauling y por qué no es una energía absoluta.',
    paragraphs: [
      'La electronegatividad expresa la tendencia relativa de un átomo enlazado a atraer densidad electrónica. Pauling es la escala más habitual, pero existen Mulliken, Allred–Rochow y Allen.',
      'No es una propiedad aislada del átomo en cualquier entorno. Estado de oxidación, hibridación y coordinación pueden modificar la atracción efectiva.',
      'Las diferencias de electronegatividad ayudan a interpretar polaridad y carácter de enlace, pero no convierten automáticamente un enlace en puramente iónico o covalente.'
    ],
    rows: [
      { term: 'Pauling', description: 'Escala relativa basada en energías de enlace.' },
      { term: 'Alta', description: 'Mayor atracción de densidad enlazante.' },
      { term: 'Baja', description: 'Mayor carácter electropositivo.' },
      { term: 'Diferencia', description: 'Indicador orientativo de polaridad.' }
    ]
  },
  {
    id: 'ionization', section: 'Átomo y electrones', label: '11 · Ionización sucesiva', title: 'Extraer electrones uno a uno',
    summary: 'Cómo leer la gráfica de energías sucesivas y sus grandes saltos.',
    paragraphs: [
      'La primera energía de ionización retira un electrón de un átomo gaseoso neutro. La segunda actúa sobre el catión +1 y así sucesivamente. Cada etapa se refiere a una especie diferente.',
      'Las energías suelen aumentar. Un salto muy grande indica que se ha agotado un conjunto de electrones relativamente externos y se empieza a romper una capa o subcapa mucho más ligada.',
      'La gráfica permite identificar esos cambios de régimen. Los valores NIST pueden ser experimentales, evaluados, semiempíricos o teóricos y deben leerse junto a su calidad.'
    ],
    rows: [
      { term: 'IE₁', description: 'Átomo neutro → catión +1.' },
      { term: 'IE₂', description: 'Catión +1 → catión +2.' },
      { term: 'Gran salto', description: 'Cambio hacia electrones de una región más interna.' },
      { term: 'Unidad', description: 'Habitualmente eV por átomo o kJ/mol.' }
    ],
    links: [{ label: 'NIST ASD · Ionization Energies', url: 'https://physics.nist.gov/PhysRefData/ASD/ionEnergy.html' }]
  },
  {
    id: 'affinity', section: 'Átomo y electrones', label: '12 · Afinidad electrónica', title: 'Añadir un electrón al átomo gaseoso',
    summary: 'Convenciones de signo y diferencia respecto a electronegatividad.',
    paragraphs: [
      'La afinidad electrónica describe el cambio energético cuando un átomo gaseoso neutro captura un electrón. Algunas fuentes informan la energía liberada como positiva y otras usan el cambio de entalpía con signo contrario.',
      'No debe confundirse con electronegatividad: la afinidad es una magnitud energética para un proceso definido, mientras que la electronegatividad es una escala relativa de átomos enlazados.',
      'Una afinidad ausente no significa necesariamente cero; puede no existir una evaluación fiable o el anión puede ser inestable.'
    ],
    rows: [
      { term: 'Proceso', description: 'X(g) + e⁻ → X⁻(g).' },
      { term: 'Signo', description: 'Depende de la convención de la fuente.' },
      { term: 'Anión', description: 'La estabilidad puede ser baja o temporal.' }
    ]
  },
  {
    id: 'radii', section: 'Tamaño y materia', label: '13 · Radios comparados', title: 'El átomo no tiene un único radio',
    summary: 'Comparación entre radios covalente, metálico, de van der Waals y cristalino.',
    paragraphs: [
      'La nube electrónica no posee una frontera rígida. Cada radio se define a partir de un contexto experimental o modelo diferente; por eso no deben mezclarse como si midieran exactamente la misma superficie.',
      'El radio covalente deriva de distancias entre átomos enlazados, el metálico de redes metálicas y el de van der Waals de contactos no enlazados. El radio cristalino depende de cómo se reparte una distancia internuclear en un sólido.',
      'La visualización concéntrica usa una escala común para comparar magnitudes disponibles, pero no implica que el átomo sea una esfera dura.'
    ],
    rows: [
      { term: 'Covalente', description: 'Mitad de una distancia de enlace bajo una convención determinada.' },
      { term: 'Metálico', description: 'Derivado de vecinos en una red metálica.' },
      { term: 'van der Waals', description: 'Contacto de átomos no enlazados.' },
      { term: 'Cristalino', description: 'Asignación dentro de una estructura cristalina.' },
      { term: 'Unidad', description: 'pm o Å; 1 Å = 100 pm.' }
    ],
    callout: 'Comparar radios exige comprobar definición, carga, coordinación, estado de espín y fuente.'
  },
  {
    id: 'ionic-radii', section: 'Tamaño y materia', label: '14 · Radios iónicos', title: 'Carga, coordinación y estado de espín',
    summary: 'Por qué un elemento puede tener muchos radios iónicos diferentes.',
    paragraphs: [
      'Al perder electrones, un catión suele contraerse; al ganarlos, un anión suele expandirse. Sin embargo, el tamaño observado también depende del número de vecinos y de la estructura del cristal.',
      'Un radio iónico debe registrarse con carga, número de coordinación y, cuando proceda, estado de espín. Un valor Fe²⁺ octaédrico de alto espín no es intercambiable con Fe²⁺ tetraédrico o de bajo espín.',
      'La pestaña Radios mantiene registros separados en vez de reducirlos a un único número engañoso.'
    ],
    rows: [
      { term: 'Carga', description: 'Estado iónico, por ejemplo +2 o −1.' },
      { term: 'Coordinación', description: 'Cantidad y geometría aproximada de vecinos.' },
      { term: 'Espín', description: 'Alto o bajo espín en determinados iones de transición.' },
      { term: 'Convención', description: 'El reparto de distancias depende del conjunto de radios empleado.' }
    ]
  },
  {
    id: 'physical', section: 'Tamaño y materia', label: '15 · Propiedades físicas', title: 'Estado, densidad y temperaturas de cambio',
    summary: 'Magnitudes macroscópicas que dependen de condiciones y muestra.',
    paragraphs: [
      'Estado estándar, densidad, fusión y ebullición describen materia macroscópica, no un átomo aislado. Dependen de presión, temperatura, fase, pureza y estructura.',
      'La densidad de un sólido no debe compararse con la de un gas sin revisar condiciones. El punto de ebullición cambia con la presión externa y algunos elementos subliman o se descomponen antes de hervir en condiciones ordinarias.',
      'Los valores básicos permanecen visibles desde physical_properties.csv aunque todavía no exista una serie termodinámica completa.'
    ],
    rows: [
      { term: 'Estado estándar', description: 'Fase bajo una condición de referencia definida.' },
      { term: 'Densidad', description: 'Masa por unidad de volumen y fase.' },
      { term: 'Fusión', description: 'Equilibrio sólido–líquido a una presión determinada.' },
      { term: 'Ebullición', description: 'Presión de vapor igual a la presión externa.' }
    ]
  },
  {
    id: 'thermodynamics', section: 'Termodinámica', label: '16 · Termodinámica', title: 'Materia, energía y condiciones',
    summary: 'Cómo leer entalpías, entropía, capacidad calorífica y puntos de fase.',
    paragraphs: [
      'La termodinámica relaciona cambios de estado, energía y equilibrio. Las magnitudes deben conservar fase, temperatura, presión y estado de referencia.',
      'La entalpía de fusión cuantifica la energía molar del paso sólido–líquido; la de vaporización, líquido–gas; la de sublimación, sólido–gas. La entropía describe el número de estados accesibles y la dispersión de energía.',
      'La ficha muestra un dato aislado cuando es lo único disponible y dibuja una curva únicamente cuando existen varios puntos compatibles.'
    ],
    rows: [
      { term: 'ΔHfus', description: 'Entalpía molar de fusión.' },
      { term: 'ΔHvap', description: 'Entalpía molar de vaporización.' },
      { term: 'Cp', description: 'Capacidad calorífica a presión constante.' },
      { term: 'S°', description: 'Entropía molar estándar.' },
      { term: 'Condiciones', description: 'Temperatura, presión y fase asociadas al registro.' }
    ]
  },
  {
    id: 'phase-map', section: 'Termodinámica', label: '17 · Mapa de fases', title: 'Fusión, ebullición, punto triple y crítico',
    summary: 'Qué significan los hitos dibujados sobre la escala de temperatura.',
    paragraphs: [
      'El mapa lineal sitúa temperaturas publicadas sobre una escala común. No es un diagrama presión–temperatura completo: sirve para localizar hitos y detectar su orden relativo.',
      'En el punto triple coexisten sólido, líquido y gas. En el punto crítico desaparece la frontera entre líquido y gas. Ambos requieren temperatura y presión específicas.',
      'Si una fuente solo proporciona texto, rango o una condición incompleta, el registro se conserva pero puede no dibujarse.'
    ],
    rows: [
      { term: 'Punto triple', description: 'Coexistencia de tres fases en equilibrio.' },
      { term: 'Punto crítico', description: 'Fin de la separación líquido–gas.' },
      { term: 'Sublimación', description: 'Paso directo entre sólido y gas.' },
      { term: 'Diagrama P–T', description: 'Representación completa de estabilidad de fases; requiere series adicionales.' }
    ]
  },
  {
    id: 'thermal-series', section: 'Termodinámica', label: '18 · Cp y presión de vapor', title: 'Curvas dependientes de temperatura',
    summary: 'Cómo interpretar las series térmicas sin inventar interpolaciones.',
    paragraphs: [
      'La capacidad calorífica Cp puede variar con la temperatura y mostrar anomalías en transiciones de fase. Un único valor de referencia no define una curva completa.',
      'La presión de vapor aumenta fuertemente con la temperatura y suele representarse en escala logarítmica. La curva está relacionada con la volatilidad y con el punto de ebullición a una presión dada.',
      'TablaElementos solo conecta puntos cuando pertenecen a una serie compatible. No rellena huecos con una función supuesta.'
    ],
    rows: [
      { term: 'Cp(T)', description: 'Capacidad calorífica frente a temperatura.' },
      { term: 'Presión de vapor', description: 'Presión de equilibrio de la fase gaseosa.' },
      { term: 'Escala log', description: 'Necesaria cuando los valores abarcan muchos órdenes de magnitud.' },
      { term: 'Serie', description: 'Conjunto de puntos con definición y condiciones compatibles.' }
    ]
  },
  {
    id: 'crystals', section: 'Materiales', label: '19 · Cristalografía', title: 'Celda unidad, simetría y parámetros de red',
    summary: 'Cómo leer el visor 3D y los datos cristalográficos.',
    paragraphs: [
      'Un cristal se describe mediante una celda unidad que se repite en el espacio. Los parámetros a, b y c son longitudes; α, β y γ son ángulos entre ejes.',
      'El sistema cristalino y el grupo espacial resumen la simetría. Estructuras como FCC, BCC, HCP o diamante corresponden a disposiciones diferentes y no deben deducirse únicamente del símbolo del elemento.',
      'El visor 3D es exacto cuando existen coordenadas estructurales suficientes y didáctico cuando solo se conoce una topología general.'
    ],
    rows: [
      { term: 'Celda unidad', description: 'Volumen mínimo cuya repetición genera el cristal.' },
      { term: 'a, b, c', description: 'Longitudes de los vectores de red.' },
      { term: 'α, β, γ', description: 'Ángulos entre vectores.' },
      { term: 'Grupo espacial', description: 'Conjunto de operaciones de simetría del cristal.' },
      { term: 'Fase', description: 'Estructura estable o metaestable bajo determinadas condiciones.' }
    ]
  },
  {
    id: 'allotropes', section: 'Materiales', label: '20 · Alótropos y fases', title: 'La misma composición, estructuras distintas',
    summary: 'Por qué carbono, hierro, estaño u oxígeno no tienen una única forma material.',
    paragraphs: [
      'Un alótropo es una forma estructural distinta del mismo elemento. Diamante y grafito son carbono, pero sus redes y enlaces producen propiedades radicalmente diferentes.',
      'Un elemento puede cambiar de fase con temperatura o presión. El hierro, por ejemplo, presenta estructuras cristalinas diferentes en distintos intervalos térmicos.',
      'El selector de fases conserva identificador, estabilidad, energía relativa, grupo espacial y parámetros de red cuando la fuente los proporciona.'
    ],
    rows: [
      { term: 'Alótropo', description: 'Forma estructural diferente de un elemento.' },
      { term: 'Polimorfismo', description: 'Más de una estructura para una misma composición.' },
      { term: 'Metaestable', description: 'Fase no mínima que puede persistir por barreras cinéticas.' },
      { term: 'Energía sobre hull', description: 'Indicador computacional de estabilidad relativa de una fase.' }
    ]
  },
  {
    id: 'isotopes', section: 'Núcleo', label: '21 · Isótopos y nucleídos', title: 'Mismo Z, distinto número de neutrones',
    summary: 'Cómo leer la tabla isotópica de cada elemento.',
    paragraphs: [
      'Los isótopos comparten número atómico Z y difieren en N. Un nucleído es una combinación concreta de protones y neutrones, identificada habitualmente por símbolo y número másico A.',
      'La tabla puede incluir masa isotópica, abundancia, vida media, espín, momentos nucleares, energía de enlace y modos de desintegración.',
      'La existencia de un nucleído conocido no implica que sea estable ni que aparezca de forma natural. Muchos se producen únicamente en reacciones nucleares.'
    ],
    rows: [
      { term: 'Z', description: 'Número de protones.' },
      { term: 'N', description: 'Número de neutrones.' },
      { term: 'A', description: 'Z + N.' },
      { term: 'Isótopo natural', description: 'Presente en un reservorio natural definido.' },
      { term: 'Radioisótopo', description: 'Nucleído inestable que se transforma espontáneamente.' }
    ],
    links: [{ label: 'IAEA · LiveChart', url: 'https://www-nds.iaea.org/relnsd/vcharthtml/VChartHTML.html' }]
  },
  {
    id: 'nuclear-map', section: 'Núcleo', label: '22 · Cartografía nuclear', title: 'Neutrones frente a vida media',
    summary: 'Cómo interpretar la gráfica logarítmica de nucleídos de un elemento.',
    paragraphs: [
      'El eje horizontal representa N y el vertical log10 de la vida media en segundos. Esta escala permite colocar desde microsegundos hasta edades geológicas en un mismo gráfico.',
      'Los nucleídos estables se sitúan en la parte superior como una categoría especial, no como una vida media infinita medida. El color indica el modo de desintegración principal.',
      'Al seleccionar un punto se abre su ficha con Z, N, A, abundancia, espín, momentos y energías Q disponibles.'
    ],
    rows: [
      { term: 'Eje N', description: 'Cantidad de neutrones.' },
      { term: 'Eje log10(s)', description: 'Orden de magnitud de la vida media.' },
      { term: 'Color', description: 'Modo principal: estable, α, β−, β+/EC, fisión u otros.' },
      { term: 'Punto seleccionado', description: 'Nucleído cuyos detalles se muestran en el panel lateral.' }
    ]
  },
  {
    id: 'decay', section: 'Núcleo', label: '23 · Vida media y decaimiento', title: 'Transformaciones nucleares y probabilidades',
    summary: 'Qué significan α, β, captura electrónica, gamma y fisión.',
    paragraphs: [
      'La vida media es el tiempo estadístico necesario para que se desintegre la mitad de una población inicial. No permite predecir cuándo se desintegrará un núcleo individual.',
      'En desintegración α se emite un núcleo de helio; en β− un neutrón se convierte en protón; en β+ o captura electrónica disminuye Z. La emisión gamma desexcita el núcleo sin cambiar Z ni A.',
      'Un nucleído puede tener varias ramas de decaimiento. La pestaña muestra el modo principal cuando es el campo disponible y conserva probabilidades adicionales en el dataset.'
    ],
    rows: [
      { term: 'α', description: 'A disminuye 4 y Z disminuye 2.' },
      { term: 'β−', description: 'Z aumenta 1; A permanece.' },
      { term: 'β+/EC', description: 'Z disminuye 1; A permanece.' },
      { term: 'γ', description: 'Desexcitación electromagnética del núcleo.' },
      { term: 'SF', description: 'Fisión espontánea en núcleos pesados.' }
    ]
  },
  {
    id: 'nuclear-quantum', section: 'Núcleo', label: '24 · Espín, momentos y Q', title: 'Propiedades cuánticas del núcleo',
    summary: 'Espín, paridad, momentos electromagnéticos y energías de reacción.',
    paragraphs: [
      'El espín nuclear I y la paridad caracterizan el momento angular y la simetría del estado. Son fundamentales para RMN, estructura hiperfina y reglas de transición.',
      'El momento dipolar magnético describe el acoplamiento con campos magnéticos y el cuadrupolar eléctrico informa sobre desviaciones de una distribución de carga esférica.',
      'Las energías Q expresan el balance de masa–energía de una reacción o desintegración. Un Q positivo indica que el proceso puede liberar energía, aunque la cinética y las barreras también importan.'
    ],
    rows: [
      { term: 'Iπ', description: 'Espín y paridad nuclear.' },
      { term: 'μ', description: 'Momento dipolar magnético.' },
      { term: 'Q eléctrico', description: 'Momento cuadrupolar de la distribución de carga.' },
      { term: 'Energía de enlace', description: 'Energía necesaria para separar el núcleo.' },
      { term: 'Qα / QEC', description: 'Balance energético de canales concretos.' }
    ]
  },
  {
    id: 'spectra', section: 'Espectroscopia', label: '25 · Espectro atómico', title: 'La huella óptica de un elemento',
    summary: 'Emisión, absorción y regiones visible, ultravioleta e infrarroja.',
    paragraphs: [
      'Las transiciones entre estados electrónicos producen o absorben fotones de energías discretas. La relación E = hc/λ conecta energía y longitud de onda.',
      'El visor coloca cada línea sobre una escala común. Las bandas de fondo indican regiones del espectro; solo una parte es visible para el ojo humano.',
      'La intensidad depende de población de niveles, temperatura, presión, instrumento y probabilidad de transición. No debe compararse entre exportaciones incompatibles como si fuera una constante del elemento.'
    ],
    rows: [
      { term: 'Emisión', description: 'Fotón producido al descender de energía.' },
      { term: 'Absorción', description: 'Fotón capturado al ascender de energía.' },
      { term: 'λ', description: 'Longitud de onda, normalmente en nm.' },
      { term: 'Especie', description: 'Átomo o ion: Fe I, Fe II, etc.' },
      { term: 'Intensidad', description: 'Magnitud dependiente del experimento y normalización.' }
    ],
    links: [{ label: 'NIST · Atomic Spectra Database', url: 'https://physics.nist.gov/PhysRefData/ASD/' }]
  },
  {
    id: 'spectral-lines', section: 'Espectroscopia', label: '26 · Líneas espectrales', title: 'Transiciones individuales y cobertura',
    summary: 'Cómo leer la tabla técnica de líneas y entender un espectro vacío.',
    paragraphs: [
      'Cada fila representa una transición con especie, longitud de onda observada o Ritz, intensidad y niveles inferior y superior cuando están disponibles.',
      'Una pestaña vacía puede deberse a que no existe un CSV NIST importado, a que el archivo es inválido o a que ninguna fila puede interpretarse. TablaElementos usa respaldo local únicamente cuando está explícitamente identificado.',
      'El hierro dispone de líneas educativas de respaldo y de un proceso de reparación focalizada para sustituir un CSV NIST vacío por una exportación oficial cuando el workflow de datos tiene red.'
    ],
    rows: [
      { term: 'Observada', description: 'Longitud medida experimentalmente.' },
      { term: 'Ritz', description: 'Longitud calculada desde niveles evaluados.' },
      { term: 'Fe I / Fe II', description: 'Hierro neutro / hierro una vez ionizado.' },
      { term: 'Respaldo', description: 'Conjunto local identificado; no se presenta como exportación oficial.' },
      { term: 'Cobertura 0', description: 'Ausencia de filas representables, no ausencia física de espectro.' }
    ]
  },
  {
    id: 'levels', section: 'Espectroscopia', label: '27 · Niveles de energía', title: 'Estados permitidos, términos y J',
    summary: 'Relación entre niveles electrónicos y líneas espectrales.',
    paragraphs: [
      'Un nivel electrónico es un estado permitido con una energía, configuración, término y momento angular total J. Las líneas conectan pares de niveles.',
      'El número de onda en cm⁻¹ es habitual porque es proporcional a la energía. El nivel fundamental se toma como referencia cero dentro de una especie.',
      'Las reglas de selección determinan qué transiciones son permitidas, débiles o prohibidas. Una transición prohibida puede ocurrir con probabilidad baja y ser importante en plasmas poco densos.'
    ],
    rows: [
      { term: 'cm⁻¹', description: 'Número de onda espectroscópico.' },
      { term: 'Término', description: 'Notación que resume acoplamiento angular y espín.' },
      { term: 'J', description: 'Momento angular electrónico total.' },
      { term: 'Ritz', description: 'Diferencia de niveles convertida en longitud de onda.' }
    ]
  },
  {
    id: 'xray', section: 'Radiación', label: '28 · Rayos X característicos', title: 'Transiciones de capas internas',
    summary: 'Líneas K, L y M y su relación con el número atómico.',
    paragraphs: [
      'Una vacante en una capa interna puede ser ocupada por un electrón de una capa superior. La diferencia de energía se emite como fotón X característico o se transfiere a un electrón Auger.',
      'Notaciones como K–L3 o L2–M4 identifican capa inicial y subcapa de origen. Las energías crecen fuertemente con Z y son útiles en fluorescencia de rayos X y microanálisis.',
      'El gráfico de barras coloca las transiciones en una escala energética logarítmica. La fuente puede ofrecer valores teóricos y experimentales separados.'
    ],
    rows: [
      { term: 'K, L, M', description: 'Capas electrónicas internas.' },
      { term: 'Kα', description: 'Familia de transiciones hacia la capa K desde L.' },
      { term: 'Kβ', description: 'Transiciones hacia K desde capas más externas.' },
      { term: 'Energía', description: 'Habitualmente expresada en eV o keV.' }
    ],
    links: [{ label: 'NIST · X-Ray Transition Energies', url: 'https://physics.nist.gov/PhysRefData/XrayTrans/' }]
  },
  {
    id: 'attenuation', section: 'Radiación', label: '29 · Atenuación de fotones', title: 'Cómo pierde intensidad un haz en la materia',
    summary: 'Coeficientes másicos, absorción de energía y bordes.',
    paragraphs: [
      'El coeficiente de atenuación másico μ/ρ resume la probabilidad total de retirar fotones del haz primario por unidad de masa atravesada. Incluye fotoeléctrico, dispersión coherente, Compton y, a energías altas, creación de pares.',
      'El coeficiente de absorción de energía μen/ρ descuenta parte de la energía que puede escapar como radiación secundaria. Ambos varían fuertemente con energía y Z.',
      'Los bordes de absorción aparecen cuando la energía supera la energía de enlace de una subcapa. Por eso la curva no siempre es suave.'
    ],
    rows: [
      { term: 'μ/ρ', description: 'Atenuación total por densidad de masa, cm²/g.' },
      { term: 'μen/ρ', description: 'Energía transferida localmente por unidad de masa.' },
      { term: 'Borde K/L/M', description: 'Discontinuidad al habilitar ionización de una subcapa.' },
      { term: 'Escala log', description: 'Permite representar de keV a MeV y muchos órdenes de magnitud.' }
    ],
    links: [{ label: 'NIST · X-Ray Mass Attenuation', url: 'https://physics.nist.gov/PhysRefData/XrayMassCoef/ElemTab/z01.html' }]
  },
  {
    id: 'xps-auger', section: 'Radiación', label: '30 · XPS y Auger', title: 'Energías de enlace y estado químico',
    summary: 'Por qué las líneas dependen del compuesto y no solo del elemento.',
    paragraphs: [
      'XPS mide la energía cinética de fotoelectrones y deduce energías de enlace de niveles internos. Los desplazamientos químicos permiten distinguir estados de oxidación, compuestos y entornos de coordinación.',
      'Los electrones Auger se producen cuando la relajación de una vacante transfiere energía a otro electrón. Su energía depende de tres niveles electrónicos y se identifica mediante notaciones como KLL.',
      'No existe una única línea XPS universal de un elemento: la calibración, el compuesto, la carga superficial y el estado químico deben conservarse en cada registro.'
    ],
    rows: [
      { term: 'Energía de enlace', description: 'Energía necesaria para extraer un electrón de un nivel.' },
      { term: 'Desplazamiento químico', description: 'Cambio producido por el entorno electrónico.' },
      { term: 'Auger', description: 'Relajación no radiativa que emite un electrón.' },
      { term: 'Estado químico', description: 'Compuesto, oxidación y coordinación asociados al valor.' }
    ],
    callout: 'La pestaña permanece vacía antes que inventar una energía elemental sin estado químico documentado.'
  },
  {
    id: 'neutrons', section: 'Radiación', label: '31 · Neutrones', title: 'Dispersión, absorción e isótopos',
    summary: 'Cómo leer longitudes y secciones eficaces neutrónicas.',
    paragraphs: [
      'La interacción neutrónica depende del núcleo y puede variar de forma drástica entre isótopos vecinos. No sigue una tendencia simple con Z como los rayos X.',
      'La longitud de dispersión coherente determina interferencia y contraste estructural. Las secciones coherente, incoherente, total y de absorción se expresan en barn.',
      'Los valores térmicos suelen referirse a neutrones de 2200 m/s. Isótopos resonantes o valores complejos requieren consultar la nota y la fuente.'
    ],
    rows: [
      { term: 'bcoh', description: 'Longitud de dispersión coherente, normalmente en fm.' },
      { term: 'σcoh', description: 'Sección eficaz de dispersión coherente.' },
      { term: 'σinc', description: 'Dispersión incoherente.' },
      { term: 'σs', description: 'Dispersión total.' },
      { term: 'σa', description: 'Absorción térmica.' },
      { term: 'barn', description: '10⁻²⁸ m².' }
    ],
    links: [{ label: 'NIST NCNR · Neutron Scattering', url: 'https://www.ncnr.nist.gov/resources/n-lengths/' }]
  },
  {
    id: 'chemistry', section: 'Química', label: '32 · Química del elemento', title: 'Reactividad, compuestos y coordinación',
    summary: 'Cómo pasar del átomo aislado a especies químicas reales.',
    paragraphs: [
      'La química depende de estados de oxidación, enlaces, ligandos, solvente, pH, potencial y cinética. La posición periódica orienta, pero no determina por sí sola una reacción concreta.',
      'La pestaña Química agrupa estados de oxidación, compuestos, materiales y registros computacionales. Cada valor debe conservar la especie o el contexto al que pertenece.',
      'Una propiedad del elemento puro no se traslada automáticamente a todos sus compuestos.'
    ],
    rows: [
      { term: 'Especie', description: 'Átomo, ion, molécula, complejo o sólido definido.' },
      { term: 'Ligando', description: 'Especie unida a un centro de coordinación.' },
      { term: 'pH / potencial', description: 'Condiciones que alteran estabilidad y oxidación.' },
      { term: 'Cinética', description: 'Velocidad y barreras, además de la favorabilidad energética.' }
    ]
  },
  {
    id: 'oxidation', section: 'Química', label: '33 · Oxidación y redox', title: 'Contabilidad formal de electrones',
    summary: 'Estados habituales, raros y dependientes del entorno.',
    paragraphs: [
      'El estado de oxidación asigna electrones mediante reglas formales. Oxidarse significa aumentar el número y reducirse significa disminuirlo.',
      'Los valores más comunes no son los únicos posibles. Estados raros pueden estabilizarse con ligandos, presiones o matrices específicas.',
      'El potencial estándar de reducción se refiere a una semirreacción concreta bajo condiciones estándar; no es un número universal del elemento aislado.'
    ],
    rows: [
      { term: 'Oxidante', description: 'Acepta electrones y se reduce.' },
      { term: 'Reductor', description: 'Cede electrones y se oxida.' },
      { term: 'E°', description: 'Potencial de una semirreacción definida.' },
      { term: 'Estado raro', description: 'Oxidación menos frecuente que requiere contexto.' }
    ]
  },
  {
    id: 'bonding', section: 'Química', label: '34 · Enlace y reactividad', title: 'Modelos iónico, covalente y metálico',
    summary: 'Límites útiles para describir enlaces reales de carácter mixto.',
    paragraphs: [
      'El enlace iónico enfatiza atracción entre cargas, el covalente compartición de densidad y el metálico deslocalización electrónica. La mayoría de sistemas reales combinan varios caracteres.',
      'Longitud, energía y orden de enlace dependen de la especie. La electronegatividad ayuda a interpretar polaridad, pero no sustituye un análisis electrónico completo.',
      'Una reacción termodinámicamente favorable puede ser lenta si existe una barrera de activación alta.'
    ],
    rows: [
      { term: 'Iónico', description: 'Predominio de interacción electrostática entre cargas.' },
      { term: 'Covalente', description: 'Densidad electrónica compartida.' },
      { term: 'Metálico', description: 'Estados electrónicos extendidos en una red.' },
      { term: 'Activación', description: 'Barrera energética que controla la velocidad.' }
    ]
  },
  {
    id: 'material-properties', section: 'Materiales', label: '35 · Propiedades del material', title: 'Mecánica, electricidad, calor y magnetismo',
    summary: 'Por qué estas magnitudes no pertenecen al átomo aislado.',
    paragraphs: [
      'Conductividad, dureza, módulos elásticos y magnetismo dependen de fase, pureza, defectos, textura y temperatura. Deben asociarse a una muestra o estructura material.',
      'Los módulos de Young, cizallamiento y compresibilidad describen respuestas distintas a una deformación. La dureza depende además del método de ensayo.',
      'La pestaña Material conserva condiciones y muestra huecos cuando no existe un valor trazable para la fase seleccionada.'
    ],
    rows: [
      { term: 'Young', description: 'Rigidez longitudinal.' },
      { term: 'Cizallamiento', description: 'Respuesta a deformación tangencial.' },
      { term: 'Bulk', description: 'Resistencia a compresión volumétrica.' },
      { term: 'Resistividad', description: 'Oposición al transporte eléctrico.' },
      { term: 'Conductividad térmica', description: 'Transporte de calor.' }
    ]
  },
  {
    id: 'transport', section: 'Materiales', label: '36 · Transporte y magnetismo', title: 'Portadores, bandas y orden colectivo',
    summary: 'Cómo estructura y temperatura gobiernan corriente, calor y respuesta magnética.',
    paragraphs: [
      'La conductividad eléctrica depende de densidad y movilidad de portadores. En sólidos, la estructura de bandas distingue metales, semiconductores y aislantes.',
      'La conductividad térmica puede involucrar electrones y vibraciones de red. Defectos e impurezas dispersan ambos tipos de portadores.',
      'Diamagnetismo, paramagnetismo, ferro-, ferri- y antiferromagnetismo describen respuestas diferentes. Las temperaturas de Curie o Néel marcan cambios de orden colectivo.'
    ],
    rows: [
      { term: 'Portador', description: 'Electrón, hueco u otra excitación que transporta carga.' },
      { term: 'Fonón', description: 'Cuanto de vibración de la red.' },
      { term: 'Curie', description: 'Pérdida de orden ferromagnético.' },
      { term: 'Néel', description: 'Transición de orden antiferromagnético.' },
      { term: 'Superconductividad', description: 'Resistencia nula y expulsión magnética bajo condiciones concretas.' }
    ]
  },
  {
    id: 'trends', section: 'Comparación', label: '37 · Tendencias periódicas', title: 'Patrones, excepciones y contexto',
    summary: 'Cómo comparar propiedades con Z sin convertir tendencias en leyes rígidas.',
    paragraphs: [
      'El radio suele disminuir a lo largo de un periodo y aumentar al bajar un grupo. Ionización y electronegatividad suelen mostrar tendencias aproximadamente opuestas.',
      'Las excepciones revelan física: estabilidad de subniveles, apantallamiento, penetración, contracción lantánida y cambios estructurales.',
      'La pestaña Tendencias sitúa el elemento dentro de una serie global. Para una comparación cuantitativa deben mantenerse definición, unidad y fuente.'
    ],
    rows: [
      { term: 'Horizontal', description: 'Aumenta Z mientras se llena una capa principal.' },
      { term: 'Vertical', description: 'Se añaden capas y apantallamiento.' },
      { term: 'Contracción lantánida', description: 'Disminución progresiva de radios por apantallamiento f imperfecto.' },
      { term: 'Excepción', description: 'Desviación informativa, no error automático.' }
    ]
  },
  {
    id: 'context', section: 'Contexto', label: '38 · Historia y usos', title: 'Descubrimiento, etimología y aplicaciones',
    summary: 'Información histórica y social que cambia con el tiempo.',
    paragraphs: [
      'La historia de un elemento incluye aislamiento, identificación, denominación y reconocimiento posterior. Descubridor y fecha pueden depender del criterio empleado.',
      'Las aplicaciones cambian con tecnología, regulación, disponibilidad y precio. Deben leerse junto a la fecha y la fuente.',
      'La utilidad de un elemento no implica seguridad: la forma química y la exposición determinan el riesgo.'
    ],
    rows: [
      { term: 'Descubrimiento', description: 'Primera observación, aislamiento o identificación aceptada.' },
      { term: 'Etimología', description: 'Origen del nombre y del símbolo.' },
      { term: 'Uso', description: 'Aplicación tecnológica situada en una fecha y sector.' },
      { term: 'Criticidad', description: 'Riesgo de suministro, sustitución e importancia económica.' }
    ]
  },
  {
    id: 'abundance', section: 'Contexto', label: '39 · Abundancia y origen', title: 'Universo, corteza, océano y organismo',
    summary: 'Reservorios que no deben compararse en una escala lineal simple.',
    paragraphs: [
      'La abundancia cósmica refleja nucleosíntesis; la terrestre incorpora diferenciación planetaria, volatilidad y geoquímica. Corteza, océanos y cuerpo humano son reservorios diferentes.',
      'Las concentraciones abarcan muchos órdenes de magnitud, por lo que las gráficas utilizan escala logarítmica cuando es apropiado.',
      'Un valor debe identificar reservorio, unidad y referencia. “Abundancia del elemento” sin contexto es una frase incompleta.'
    ],
    rows: [
      { term: 'Cósmica', description: 'Abundancia en el universo o sistema solar.' },
      { term: 'Corteza', description: 'Concentración en la corteza terrestre.' },
      { term: 'Océano', description: 'Concentración disuelta o total en agua marina.' },
      { term: 'Humana', description: 'Fracción o masa en el organismo.' },
      { term: 'ppm / ppb', description: 'Unidades de concentración que requieren base definida.' }
    ]
  },
  {
    id: 'biology', section: 'Contexto', label: '40 · Biología y toxicidad', title: 'Esencialidad, dosis y especie química',
    summary: 'Por qué “elemento tóxico” es a menudo una simplificación insuficiente.',
    paragraphs: [
      'Un elemento puede ser esencial a dosis pequeñas y tóxico a dosis altas. La forma química, solubilidad, vía de exposición y estado de oxidación son determinantes.',
      'LD50 depende de especie, vía, tiempo y compuesto. No debe presentarse como un único valor universal del elemento.',
      'Carcinogenicidad, bioacumulación y neurotoxicidad requieren fuentes toxicológicas específicas y no pueden deducirse de la tabla periódica.'
    ],
    rows: [
      { term: 'Esencial', description: 'Necesario para una función biológica demostrada.' },
      { term: 'Oligoelemento', description: 'Necesario en cantidades pequeñas.' },
      { term: 'Especiación', description: 'Forma química concreta presente.' },
      { term: 'Dosis', description: 'Cantidad por masa, tiempo o superficie.' },
      { term: 'Vía', description: 'Inhalación, ingestión, contacto u otra exposición.' }
    ]
  },
  {
    id: 'navigation', section: 'Uso de la aplicación', label: '41 · Navegación táctil y zoom', title: 'Moverse por la tabla y por las fichas',
    summary: 'Rueda, arrastre, gestos, pestañas y encuadre.',
    paragraphs: [
      'La rueda amplía alrededor del cursor y el arrastre desplaza la tabla. El porcentaje restablece el encuadre y el botón 18/32 alterna las dos disposiciones.',
      'La barra de pestañas se desplaza horizontalmente con gesto táctil, rueda, trackpad o flechas laterales. Al acercar el puntero a un borde, la lista avanza automáticamente.',
      'Al abrir una ficha se realiza un pequeño desplazamiento de demostración para indicar que hay más pestañas fuera del área visible.'
    ],
    rows: [
      { term: 'Rueda', description: 'Zoom continuo anclado al cursor.' },
      { term: 'Arrastre', description: 'Desplazamiento de la tabla.' },
      { term: 'Swipe', description: 'Desplazamiento táctil horizontal de pestañas.' },
      { term: 'Bordes', description: 'Autoavance mientras el puntero permanece cerca.' },
      { term: '18/32', description: 'Alternancia de disposición periódica.' }
    ]
  },
  {
    id: 'filters', section: 'Uso de la aplicación', label: '42 · Filtros', title: 'Combinar criterios sin perder contexto',
    summary: 'Lógica O dentro de un bloque y Y entre bloques.',
    paragraphs: [
      'Las opciones de una misma familia se combinan mediante O: por ejemplo, halógeno o gas noble. Los bloques diferentes se intersectan mediante Y: categoría y periodo y rango de densidad.',
      'Los rangos numéricos admiten dos tiradores y edición manual de extremos. La opción “sin dato” decide si se mantienen elementos cuya propiedad no está disponible.',
      'Los elementos coincidentes se intensifican y el resto se atenúa. Un resultado cero puede ser una combinación legítimamente imposible, no un fallo del filtro.'
    ],
    rows: [
      { term: 'O', description: 'Alternativas dentro del mismo grupo.' },
      { term: 'Y', description: 'Intersección entre grupos diferentes.' },
      { term: 'Rango', description: 'Mínimo y máximo inclusivos.' },
      { term: 'Sin dato', description: 'Tratamiento explícito de valores ausentes.' }
    ]
  },
  {
    id: 'comparison', section: 'Comparación', label: '43 · Comparador total', title: 'Comparar sin mezclar magnitudes',
    summary: 'Ámbitos especializados y coherencia metrológica.',
    paragraphs: [
      'El comparador puede reunir varios elementos y cambiar de ámbito. Cada ámbito selecciona propiedades compatibles: electrónica, radios, cristal, nuclear, termodinámica o radiación.',
      'Una comparación válida usa la misma definición, unidad, fase, condición y fuente. Un radio covalente no debe enfrentarse directamente a uno de van der Waals.',
      'Los recuentos de registros indican cobertura, no calidad ni magnitud física. Tener más filas no convierte automáticamente un elemento en “más complejo”.'
    ],
    rows: [
      { term: 'Ámbito', description: 'Conjunto coherente de propiedades comparadas.' },
      { term: 'Unidad', description: 'Debe ser compatible o convertirse explícitamente.' },
      { term: 'Condición', description: 'Temperatura, presión, fase, carga o isótopo.' },
      { term: 'Cobertura', description: 'Cantidad de registros disponibles, no valor físico.' }
    ],
    callout: 'La coherencia de definición es más importante que el número de cifras mostradas.'
  },
  {
    id: 'missing-data', section: 'Calidad de datos', label: '44 · Datos ausentes y conflictos', title: 'Qué significa un hueco, un rango o dos valores distintos',
    summary: 'Cómo interpretar cobertura incompleta sin inventar información.',
    paragraphs: [
      'Un campo vacío puede significar no aplicable, no medido, no evaluado, no importado o fuente temporalmente inaccesible. La interfaz evita convertir esos casos en cero.',
      'Dos fuentes pueden discrepar por definición, fase, temperatura, método, muestra o revisión. Los valores no deben fusionarse silenciosamente; se conservan fuente y notas.',
      'Los procesos de enriquecimiento remoto se ejecutan fuera del uso normal de la web. El despliegue consume CSV versionados para que una caída externa no borre ni altere la aplicación.'
    ],
    rows: [
      { term: '—', description: 'Dato no disponible o no aplicable; nunca equivale automáticamente a cero.' },
      { term: 'Rango', description: 'Variación física, incertidumbre o conjunto de mediciones.' },
      { term: 'Conflicto', description: 'Valores de fuentes o condiciones distintas.' },
      { term: 'Respaldo', description: 'Dato local identificado que evita una pestaña vacía sin fingir procedencia.' },
      { term: 'Versionado', description: 'CSV persistido en la carpeta del elemento.' }
    ],
    callout: 'TablaElementos prefiere mostrar una ausencia explicada antes que completar una cifra mediante invención o una conversión dudosa.'
  },
  {
    id: 'sources', section: 'Calidad de datos', label: '45 · Fuentes y trazabilidad', title: 'Procedencia, fecha, método y calidad',
    summary: 'Cómo comprobar de dónde procede cada registro.',
    paragraphs: [
      'Cada elemento posee su propia carpeta y CSV por dominio. Las filas deben conservar proveedor, URL, fecha de recuperación, unidad, condiciones y notas cuando sean relevantes.',
      'PubChem aporta identidad y anotaciones generales; CIAAW pesos atómicos; NIST espectros, niveles, rayos X, atenuación y datos neutrónicos; IAEA propiedades nucleares; Materials Project fases calculadas cuando existe clave.',
      'Un valor puede ser experimental, evaluado, calculado, semiempírico, teórico o derivado por TablaElementos. La etiqueta de procedencia forma parte del dato y no es un detalle opcional.'
    ],
    rows: [
      { term: 'Experimental', description: 'Resultado de una medición.' },
      { term: 'Evaluado', description: 'Valor revisado y recomendado por especialistas.' },
      { term: 'Calculado', description: 'Resultado de un modelo teórico o computacional.' },
      { term: 'Derivado', description: 'Transformación documentada a partir de datos locales.' },
      { term: 'retrieved_at', description: 'Fecha en que se obtuvo o actualizó la fuente.' },
      { term: 'sources.csv', description: 'Inventario de proveedores y estado de cada archivo del elemento.' }
    ],
    links: [
      { label: 'PubChem', url: 'https://pubchem.ncbi.nlm.nih.gov/periodic-table/' },
      { label: 'CIAAW', url: 'https://ciaaw.org/atomic-weights.htm' },
      { label: 'NIST ASD', url: 'https://physics.nist.gov/PhysRefData/ASD/' },
      { label: 'IAEA LiveChart', url: 'https://www-nds.iaea.org/relnsd/vcharthtml/VChartHTML.html' },
      { label: 'Materials Project', url: 'https://materialsproject.org/' }
    ]
  }
];

export const GUIDE_TOPIC_LABELS = Object.fromEntries(
  GUIDE_TOPICS.map((topic) => [topic.id, topic.title])
) as Record<string, string>;
