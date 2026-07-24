<script lang="ts">
  import { createEventDispatcher, onMount } from 'svelte';

  interface GuideLink { label: string; url: string; }
  interface GuideRow { term: string; description: string; }
  interface GuideTopic {
    id: string;
    label: string;
    title: string;
    paragraphs: string[];
    rows?: GuideRow[];
    callout?: string;
    links?: GuideLink[];
  }

  export let open = false;

  const dispatch = createEventDispatcher<{ close: void }>();
  let activeId = 'vision';
  let scrollElement: HTMLDivElement;

  const topics: GuideTopic[] = [
    {
      id: 'vision', label: '1 · Qué estás viendo', title: 'Qué estás viendo',
      paragraphs: [
        'Esta aplicación representa la tabla periódica como un mapa científico ampliable. La posición de cada elemento resume estructura electrónica, regularidades químicas y relaciones con sus vecinos.',
        'La vista general conserva número atómico, símbolo y nombre. Al ampliar aparecen propiedades esenciales; en inspección, la casilla se convierte en un resumen técnico. Un clic abre la ficha maestra con todos los dominios disponibles.'
      ],
      rows: [
        { term: 'Filas', description: 'Periodos: reflejan el llenado progresivo de niveles electrónicos.' },
        { term: 'Columnas', description: 'Grupos: reúnen patrones de valencia y comportamientos relacionados.' },
        { term: 'Colores', description: 'Familias químicas y regiones de la tabla.' }
      ],
      callout: 'La tabla periódica no es una lista ordenada: es una representación compacta de regularidades físicas y químicas.',
      links: [
        { label: 'IUPAC · Periodic Table', url: 'https://iupac.org/what-we-do/periodic-table-of-elements/' },
        { label: 'PubChem · Periodic Table', url: 'https://pubchem.ncbi.nlm.nih.gov/periodic-table/' }
      ]
    },
    {
      id: 'anatomia', label: '2 · Anatomía de la casilla', title: 'Cómo leer una casilla progresiva',
      paragraphs: [
        'La casilla mínima muestra únicamente los tres identificadores universales. La ampliación revela propiedades en capas para conservar legibilidad cuando se observa la tabla completa.',
        'Los campos periféricos proceden del resumen científico local. No son etiquetas decorativas: enlazan la vista general con la ficha maestra.'
      ],
      rows: [
        { term: 'Superior izquierda', description: 'Número atómico Z.' },
        { term: 'Centro', description: 'Símbolo y nombre.' },
        { term: 'Perímetro ampliado', description: 'Masa, configuración, energías, radio, densidad y estado.' }
      ]
    },
    {
      id: 'identidad', label: '3 · Z, símbolo y nombre', title: 'Identidad del elemento',
      paragraphs: [
        'El número atómico Z es la cantidad de protones del núcleo y define el elemento. Cambiar Z significa cambiar de elemento. En un átomo neutro, el número de electrones coincide con Z.',
        'El símbolo es la abreviatura internacional. Algunos símbolos conservan raíces históricas o latinas, como Fe, Na, K o W.'
      ],
      rows: [
        { term: 'Z', description: 'Protones del núcleo y posición ordinal.' },
        { term: 'Símbolo', description: 'Abreviatura normalizada y sensible a mayúsculas.' },
        { term: 'Nombre', description: 'Denominación lingüística del elemento.' }
      ]
    },
    {
      id: 'organizacion', label: '4 · Grupo, periodo y bloque', title: 'La arquitectura de la tabla',
      paragraphs: [
        'Los grupos son columnas numeradas del 1 al 18. Los periodos son filas. El bloque s, p, d o f identifica el tipo de subnivel que recibe el electrón diferenciador.',
        'La tabla corta separa el bloque f para ahorrar anchura; la tabla larga lo integra dentro de los periodos 6 y 7.'
      ],
      rows: [
        { term: 'Bloque s', description: 'Zona izquierda y helio por configuración.' },
        { term: 'Bloque p', description: 'Zona derecha, grupos 13 a 18.' },
        { term: 'Bloque d', description: 'Metales de transición.' },
        { term: 'Bloque f', description: 'Lantánidos y actínidos.' }
      ]
    },
    {
      id: 'familias', label: '5 · Familias químicas', title: 'Categorías y familias',
      paragraphs: [
        'Las familias resaltan semejanzas útiles: alcalinos, alcalinotérreos, halógenos, gases nobles, metales de transición, lantánidos y actínidos.',
        'Algunas fronteras son convencionales. La clasificación de metaloides o metales postransición puede variar entre fuentes.'
      ],
      rows: [
        { term: 'Alcalinos', description: 'Metales reactivos del grupo 1, salvo hidrógeno.' },
        { term: 'Halógenos', description: 'Grupo 17, con fuerte tendencia a formar sales.' },
        { term: 'Gases nobles', description: 'Grupo 18, generalmente poco reactivo en condiciones ordinarias.' },
        { term: 'Transición', description: 'Bloque d, con química de coordinación variada.' }
      ]
    },
    {
      id: 'masa', label: '6 · Masa y peso atómico', title: 'Masa atómica, número másico y peso estándar',
      paragraphs: [
        'La masa de un átomo depende de su isótopo. El número másico A es la suma entera de protones y neutrones. El peso atómico estándar puede ser decimal porque representa composiciones isotópicas naturales.',
        'CIAAW publica valores e intervalos recomendados. Un intervalo refleja variaciones reales entre materiales terrestres, no falta de precisión.'
      ],
      rows: [
        { term: 'u', description: 'Unidad de masa atómica unificada.' },
        { term: 'A', description: 'Protones + neutrones de un nucleído.' },
        { term: 'Peso estándar', description: 'Valor recomendado para materiales normales.' }
      ],
      links: [{ label: 'CIAAW · Atomic Weights', url: 'https://ciaaw.org/atomic-weights.htm' }]
    },
    {
      id: 'configuracion', label: '7 · Configuración electrónica', title: 'Capas, subniveles y orbitales',
      paragraphs: [
        'La configuración electrónica describe la distribución de electrones. La notación abreviada usa un gas noble como núcleo y añade los electrones restantes.',
        'Las órbitas del simulador 3D son didácticas. La descripción cuántica real utiliza orbitales y distribuciones de probabilidad, no trayectorias planetarias rígidas.'
      ],
      rows: [
        { term: 'n', description: 'Nivel principal o capa.' },
        { term: 's, p, d, f', description: 'Subniveles con capacidades y formas diferentes.' },
        { term: 'Valencia', description: 'Electrones que suelen dominar enlaces y reactividad.' }
      ]
    },
    {
      id: 'electronegatividad', label: '8 · Electronegatividad', title: 'Atracción de densidad electrónica',
      paragraphs: [
        'La electronegatividad expresa la tendencia relativa de un átomo enlazado a atraer densidad electrónica. La escala de Pauling es la más habitual, pero no es la única.',
        'Se utiliza para interpretar polaridad y carácter de enlace. No es una energía absoluta ni una propiedad aislada del entorno químico.'
      ],
      rows: [
        { term: 'Alta', description: 'Mayor atracción relativa de electrones enlazantes.' },
        { term: 'Baja', description: 'Mayor carácter electropositivo.' },
        { term: 'Diferencia', description: 'Ayuda a estimar polaridad, no dicta por sí sola el enlace.' }
      ]
    },
    {
      id: 'energias', label: '9 · Ionización y afinidad', title: 'Retirar o incorporar electrones',
      paragraphs: [
        'La primera energía de ionización es la energía necesaria para retirar un electrón de un átomo gaseoso neutro. Las ionizaciones sucesivas suelen exigir más energía.',
        'La afinidad electrónica describe el cambio energético al añadir un electrón a un átomo gaseoso. Debe comprobarse la convención de signo de cada fuente.'
      ],
      rows: [
        { term: 'Ionización alta', description: 'Electrón externo fuertemente ligado.' },
        { term: 'Gran salto', description: 'Puede indicar que se empieza a romper una capa interna.' },
        { term: 'Afinidad', description: 'Relacionada con la estabilidad del anión gaseoso.' }
      ]
    },
    {
      id: 'radio', label: '10 · Radio atómico', title: 'Un tamaño sin frontera rígida',
      paragraphs: [
        'La nube electrónica no posee un borde geométrico exacto. Por eso existen radios covalentes, metálicos, iónicos y de van der Waals.',
        'Dos fuentes pueden dar valores distintos porque miden contextos distintos. Los cationes suelen contraerse y los aniones suelen expandirse respecto al átomo neutro.'
      ],
      rows: [
        { term: 'Covalente', description: 'Derivado de distancias entre núcleos enlazados.' },
        { term: 'Metálico', description: 'Estimado en estructuras metálicas.' },
        { term: 'van der Waals', description: 'Contacto entre átomos no enlazados.' }
      ]
    },
    {
      id: 'fisicas', label: '11 · Estado, densidad y fases', title: 'Propiedades físicas de referencia',
      paragraphs: [
        'El estado estándar indica una condición de referencia. Presión y temperatura pueden cambiar la fase. La densidad también depende de fase, temperatura, pureza y estructura cristalina.',
        'Los puntos de fusión y ebullición son equilibrios a presiones determinadas, no fronteras universales independientes del entorno.'
      ],
      rows: [
        { term: 'Densidad', description: 'Masa por unidad de volumen.' },
        { term: 'Fusión', description: 'Equilibrio sólido-líquido.' },
        { term: 'Ebullición', description: 'Presión de vapor igual a la presión externa.' }
      ]
    },
    {
      id: 'isotopos', label: '12 · Isótopos y nucleídos', title: 'Variaciones del mismo elemento',
      paragraphs: [
        'Los isótopos tienen el mismo número de protones y diferente número de neutrones. Cada combinación concreta de Z y N es un nucleído.',
        'La tabla de isótopos puede incluir masa, abundancia, vida media, espín y modos de desintegración.'
      ],
      rows: [
        { term: 'N', description: 'Número de neutrones.' },
        { term: 'A', description: 'Z + N.' },
        { term: 'Vida media', description: 'Tiempo estadístico para reducir una población a la mitad.' },
        { term: 'Abundancia', description: 'Fracción en una muestra o reservorio definido.' }
      ],
      links: [{ label: 'IAEA · LiveChart', url: 'https://www-nds.iaea.org/relnsd/vcharthtml/VChartHTML.html' }]
    },
    {
      id: 'espectro', label: '13 · Espectros y líneas', title: 'Huellas ópticas del átomo',
      paragraphs: [
        'Las transiciones electrónicas emiten o absorben fotones con energías concretas. Las líneas resultantes son características del átomo y de su estado de ionización.',
        'La intensidad depende del experimento, población de niveles, temperatura y probabilidad de transición. No debe compararse ciegamente entre datasets distintos.'
      ],
      rows: [
        { term: 'λ', description: 'Longitud de onda.' },
        { term: 'Emisión', description: 'Fotón producido al descender de energía.' },
        { term: 'Absorción', description: 'Fotón capturado al ascender de energía.' },
        { term: 'UV/visible/IR', description: 'Regiones del espectro electromagnético.' }
      ],
      links: [{ label: 'NIST · Atomic Spectra Database', url: 'https://physics.nist.gov/PhysRefData/ASD/' }]
    },
    {
      id: 'niveles', label: '14 · Niveles de energía', title: 'Estados permitidos y transiciones',
      paragraphs: [
        'Los niveles son estados electrónicos permitidos. NIST publica configuraciones, términos, J, energías e incertidumbres evaluadas.',
        'Una línea conecta un nivel inferior y otro superior. Las reglas de selección condicionan qué transiciones son intensas, débiles o prohibidas.'
      ],
      rows: [
        { term: 'cm⁻¹', description: 'Número de onda usado en espectroscopia.' },
        { term: 'J', description: 'Momento angular total.' },
        { term: 'Término', description: 'Notación de propiedades angulares y de espín.' }
      ]
    },
    {
      id: 'quimica', label: '15 · Química y materiales', title: 'Compuestos, estados de oxidación y materiales',
      paragraphs: [
        'Los estados de oxidación son una contabilidad formal útil para reacciones redox. No equivalen siempre a cargas físicas localizadas.',
        'Las propiedades de un material dependen del elemento, pero también de estructura cristalina, defectos, aleación, tamaño de grano y procesado.'
      ],
      rows: [
        { term: 'Oxidación', description: 'Número formal asignado según reglas químicas.' },
        { term: 'Compuesto', description: 'Sustancia con composición definida.' },
        { term: 'Material', description: 'Sistema macroscópico condicionado por estructura y procesado.' }
      ]
    },
    {
      id: 'contexto', label: '16 · Historia y contexto', title: 'Descubrimiento, usos y consecuencias',
      paragraphs: [
        'La relevancia de un elemento incluye su descubrimiento, abundancia, minerales, funciones biológicas, toxicidad, impacto ambiental y aplicaciones industriales.',
        'Los datos económicos, regulatorios y de seguridad cambian con el tiempo; deben leerse junto a fecha y fuente.'
      ],
      rows: [
        { term: 'Geoquímica', description: 'Distribución en minerales y reservorios.' },
        { term: 'Biología', description: 'Esencialidad, metabolismo, medicina o toxicidad.' },
        { term: 'Industria', description: 'Producción, aplicaciones y cadenas de suministro.' }
      ]
    },
    {
      id: 'navegacion', label: '17 · Navegación y zoom', title: 'Exploración progresiva',
      paragraphs: [
        'La rueda amplía tomando como ancla el cursor. Arrastrar desplaza la tabla incluso si el gesto comienza sobre una casilla. Un clic limpio abre la ficha.',
        'El porcentaje de zoom sirve también para restablecer y encajar. El botón 18/32 alterna entre tabla corta y larga.'
      ],
      rows: [
        { term: 'General', description: 'Z, símbolo y nombre.' },
        { term: 'Intermedia', description: 'Masa y estado.' },
        { term: 'Ampliada', description: 'Configuración, radio, densidad y electronegatividad.' },
        { term: 'Inspección', description: 'Resumen científico completo dentro de la casilla.' }
      ],
      callout: 'Alt + clic sobre Información abre el diagnóstico técnico interno.'
    },
    {
      id: 'fuentes', label: '18 · Fuentes y límites', title: 'Procedencia y lectura responsable',
      paragraphs: [
        'PubChem aporta propiedades generales; CIAAW, pesos atómicos; NIST, espectros y niveles; IAEA, datos nucleares.',
        'Antes de comparar valores deben comprobarse unidades, definición, condiciones experimentales, fecha y redondeo.'
      ],
      rows: [
        { term: 'PubChem', description: 'Identidad y propiedades generales.' },
        { term: 'CIAAW', description: 'Pesos atómicos y composición isotópica.' },
        { term: 'NIST ASD', description: 'Líneas, niveles e ionización.' },
        { term: 'IAEA', description: 'Estados nucleares y desintegraciones.' }
      ]
    },
    {
      id: 'tendencias', label: '19 · Tendencias periódicas', title: 'Cómo cambian las propiedades por la tabla',
      paragraphs: [
        'Muchas propiedades muestran tendencias, no leyes absolutas. El radio suele disminuir de izquierda a derecha y aumentar hacia abajo; la ionización y la electronegatividad suelen comportarse de forma aproximadamente opuesta.',
        'Las excepciones contienen información física: subniveles semillenos, apantallamiento, contracción lantánida y cambios estructurales alteran patrones simples.'
      ],
      rows: [
        { term: 'Horizontal', description: 'Aumenta la carga nuclear mientras se llena una misma capa principal.' },
        { term: 'Vertical', description: 'Se añaden capas y aumenta el apantallamiento.' },
        { term: 'Excepciones', description: 'No son errores; revelan estructura electrónica.' }
      ]
    },
    {
      id: 'carga-efectiva', label: '20 · Carga nuclear efectiva', title: 'Atracción neta y apantallamiento',
      paragraphs: [
        'Los electrones internos reducen parcialmente la atracción que siente un electrón externo. La carga nuclear efectiva combina la carga positiva del núcleo y ese apantallamiento.',
        'Este concepto ayuda a explicar radio, ionización y tendencias periódicas. No existe un único valor exacto independiente del orbital y del modelo.'
      ],
      rows: [
        { term: 'Núcleo', description: 'Atrae a los electrones mediante carga positiva.' },
        { term: 'Apantallamiento', description: 'Electrones internos reducen la atracción neta.' },
        { term: 'Penetración', description: 'Orbitales distintos se acercan de forma diferente al núcleo.' }
      ]
    },
    {
      id: 'llenado', label: '21 · Llenado y excepciones', title: 'Aufbau, Hund y Pauli',
      paragraphs: [
        'El principio de Aufbau ofrece un orden aproximado de llenado. La regla de Hund favorece ocupaciones desapareadas en orbitales degenerados y Pauli limita cada orbital a dos electrones con espines opuestos.',
        'Existen configuraciones aparentes excepcionales, especialmente en transición, porque las energías de subniveles próximos son muy parecidas.'
      ],
      rows: [
        { term: 'Aufbau', description: 'Se ocupan primero estados de menor energía aproximada.' },
        { term: 'Hund', description: 'Se maximiza inicialmente la ocupación desapareada.' },
        { term: 'Pauli', description: 'No hay dos electrones con los cuatro números cuánticos iguales.' }
      ]
    },
    {
      id: 'oxidacion', label: '22 · Oxidación y redox', title: 'Transferencia formal de electrones',
      paragraphs: [
        'Oxidación significa aumento del estado de oxidación y reducción significa disminución. Ambos procesos ocurren conjuntamente.',
        'Los estados accesibles dependen de configuración electrónica, ligandos, medio, potencial y energía de estabilización.'
      ],
      rows: [
        { term: 'Oxidante', description: 'Acepta electrones y se reduce.' },
        { term: 'Reductor', description: 'Cede electrones y se oxida.' },
        { term: 'Potencial', description: 'Mide tendencia redox bajo condiciones definidas.' }
      ]
    },
    {
      id: 'enlace', label: '23 · Enlace y reactividad', title: 'Iónico, covalente, metálico y más allá',
      paragraphs: [
        'Los modelos iónico, covalente y metálico describen límites útiles. Muchos enlaces reales tienen carácter mixto.',
        'La reactividad depende de estructura electrónica, energía, entorno, fase, superficie y cinética. Una reacción favorable termodinámicamente puede ser lenta.'
      ],
      rows: [
        { term: 'Iónico', description: 'Atracción entre especies con carga dominante.' },
        { term: 'Covalente', description: 'Compartición de densidad electrónica.' },
        { term: 'Metálico', description: 'Electrones deslocalizados en una red de núcleos.' },
        { term: 'Cinética', description: 'Velocidad y barreras de reacción.' }
      ]
    },
    {
      id: 'cristales', label: '24 · Cristales y alótropos', title: 'La estructura cambia las propiedades',
      paragraphs: [
        'Un mismo elemento puede formar estructuras cristalinas o alótropos distintos. Carbono, fósforo, azufre, estaño y oxígeno ofrecen ejemplos conocidos.',
        'La estructura controla dureza, conductividad, color, magnetismo y estabilidad. No basta con conocer la composición elemental.'
      ],
      rows: [
        { term: 'Alótropo', description: 'Forma estructural diferente del mismo elemento.' },
        { term: 'Red cristalina', description: 'Orden periódico de átomos o iones.' },
        { term: 'Polimorfismo', description: 'Más de una estructura para una misma composición.' }
      ]
    },
    {
      id: 'transporte', label: '25 · Electricidad, calor y magnetismo', title: 'Propiedades de transporte y respuesta',
      paragraphs: [
        'Conductividad eléctrica y térmica dependen de portadores, bandas electrónicas, estructura y defectos. Los metales suelen conducir bien, pero hay enormes diferencias entre ellos.',
        'La respuesta magnética depende de electrones desapareados y de interacciones colectivas. Diamagnetismo, paramagnetismo, ferromagnetismo y antiferromagnetismo describen comportamientos diferentes.'
      ],
      rows: [
        { term: 'Conductividad', description: 'Capacidad de transportar carga o calor.' },
        { term: 'Paramagnetismo', description: 'Respuesta asociada a momentos magnéticos no compensados.' },
        { term: 'Ferromagnetismo', description: 'Orden colectivo que puede mantener magnetización.' }
      ]
    },
    {
      id: 'abundancia', label: '26 · Abundancia y origen cósmico', title: 'De la nucleosíntesis al planeta',
      paragraphs: [
        'Hidrógeno y helio proceden en gran medida de la nucleosíntesis primordial. Muchos elementos más pesados se formaron en estrellas, supernovas y eventos de captura de neutrones.',
        'La abundancia terrestre no coincide con la cósmica. Diferenciación planetaria, volatilidad y geoquímica redistribuyen los elementos entre núcleo, manto, corteza, océanos y atmósfera.'
      ],
      rows: [
        { term: 'Primordial', description: 'Producción en los primeros minutos del universo.' },
        { term: 'Estelar', description: 'Fusión y procesos nucleares dentro de estrellas.' },
        { term: 'Explosiva', description: 'Supernovas y eventos ricos en neutrones.' },
        { term: 'Planetaria', description: 'Redistribución por química y diferenciación.' }
      ]
    },
    {
      id: 'biologia', label: '27 · Biología, toxicidad y dosis', title: 'Esencial no significa inocuo',
      paragraphs: [
        'Un elemento puede ser esencial a dosis pequeñas y tóxico a dosis altas. La forma química, vía de exposición, solubilidad y estado de oxidación son determinantes.',
        'La toxicidad no puede deducirse únicamente de la posición periódica. Deben consultarse compuestos concretos, límites regulatorios y contexto médico.'
      ],
      rows: [
        { term: 'Esencialidad', description: 'Necesidad biológica demostrada en un organismo.' },
        { term: 'Dosis', description: 'Cantidad recibida por masa, tiempo o superficie.' },
        { term: 'Especiación', description: 'Forma química concreta presente en el medio.' }
      ]
    },
    {
      id: 'radiacion', label: '28 · Radiación y fotónica', title: 'Interacción con fotones y partículas',
      paragraphs: [
        'Los elementos absorben, emiten y dispersan radiación. La respuesta depende de niveles electrónicos, estructura del material y energía incidente.',
        'En rayos X, óptica, láseres, detectores y protección radiológica importan propiedades diferentes: número atómico, densidad, bandas, fluorescencia y secciones eficaces.'
      ],
      rows: [
        { term: 'Absorción', description: 'Transferencia de energía al sistema.' },
        { term: 'Emisión', description: 'Liberación de fotones tras una transición.' },
        { term: 'Dispersión', description: 'Cambio de dirección o energía de la radiación.' },
        { term: 'Fluorescencia', description: 'Emisión posterior a una excitación.' }
      ]
    },
    {
      id: 'comparar', label: '29 · Cómo comparar elementos', title: 'Comparar sin mezclar magnitudes',
      paragraphs: [
        'Una comparación válida usa la misma definición, unidad, condición y fuente siempre que sea posible. Un radio covalente no debe enfrentarse directamente a un radio de van der Waals.',
        'El comparador permite cambiar de ámbito. La comparación global orienta; las pestañas especializadas permiten interpretar diferencias con más rigor.'
      ],
      rows: [
        { term: 'Primero', description: 'Comprobar unidad y definición.' },
        { term: 'Después', description: 'Revisar condición, fase y fecha.' },
        { term: 'Finalmente', description: 'Interpretar tendencia y excepciones.' }
      ],
      callout: 'Más cifras no significan automáticamente una comparación mejor: la coherencia metrológica es prioritaria.'
    },
    {
      id: 'calidad', label: '30 · Calidad y procedencia', title: 'Datos evaluados, incertidumbre y ausencia',
      paragraphs: [
        'Un valor puede ser experimental, evaluado, calculado o estimado. La incertidumbre expresa conocimiento limitado, no necesariamente mala calidad.',
        'Una celda vacía puede significar que la propiedad no está definida, no se ha medido, no se ha importado o no aplica. La pestaña Fuentes distingue disponibilidad local y procedencia.'
      ],
      rows: [
        { term: 'Experimental', description: 'Derivado de una medición.' },
        { term: 'Evaluado', description: 'Revisado y recomendado por especialistas.' },
        { term: 'Calculado', description: 'Obtenido mediante un modelo teórico o computacional.' },
        { term: 'Ausente', description: 'No debe interpretarse automáticamente como valor cero.' }
      ],
      links: [
        { label: 'PubChem', url: 'https://pubchem.ncbi.nlm.nih.gov/periodic-table/' },
        { label: 'CIAAW', url: 'https://ciaaw.org/atomic-weights.htm' },
        { label: 'NIST ASD', url: 'https://physics.nist.gov/PhysRefData/ASD/' },
        { label: 'IAEA LiveChart', url: 'https://www-nds.iaea.org/relnsd/vcharthtml/VChartHTML.html' }
      ]
    }
  ];

  let activeTopic: GuideTopic = topics[0]!;
  $: activeTopic = topics.find((topic) => topic.id === activeId) ?? topics[0]!;

  function selectTopic(id: string): void {
    activeId = id;
    scrollElement?.scrollTo({ top: 0, behavior: 'smooth' });
  }

  function closeFromBackdrop(event: MouseEvent): void {
    if (event.currentTarget === event.target) dispatch('close');
  }

  onMount(() => {
    const handleKey = (event: KeyboardEvent): void => {
      if (open && event.key === 'Escape') dispatch('close');
    };
    window.addEventListener('keydown', handleKey);
    return () => window.removeEventListener('keydown', handleKey);
  });
</script>

{#if open}
  <div class="periodic-guide-backdrop" role="presentation" on:click={closeFromBackdrop}>
    <div class="periodic-guide" role="dialog" aria-modal="true" aria-label="Guía completa de la tabla periódica">
      <header class="periodic-guide-head">
        <div>
          <p>Guía científica · 30 capítulos</p>
          <h2>Tabla periódica de los elementos</h2>
          <small>Conceptos, tendencias, propiedades, espectros, isótopos, materiales, navegación y calidad de datos.</small>
        </div>
        <button type="button" aria-label="Cerrar guía" title="Cerrar" on:click={() => dispatch('close')}>
          <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 5l14 14M19 5 5 19"></path></svg>
        </button>
      </header>

      <nav class="periodic-guide-tabs" aria-label="Temas de la guía">
        {#each topics as topic}
          <button class:active={activeId === topic.id} type="button" on:click={() => selectTopic(topic.id)}>{topic.label}</button>
        {/each}
      </nav>

      <div bind:this={scrollElement} class="periodic-guide-scroll" role="region" aria-label="Contenido de la guía">
        <section class="periodic-guide-section">
          <h3>{activeTopic.title}</h3>
          {#each activeTopic.paragraphs as paragraph}<p>{paragraph}</p>{/each}

          {#if activeTopic.rows?.length}
            <div class="periodic-guide-table">
              {#each activeTopic.rows as row}
                <div><b>{row.term}</b><span>{row.description}</span></div>
              {/each}
            </div>
          {/if}

          {#if activeTopic.callout}<div class="periodic-guide-callout">{activeTopic.callout}</div>{/if}

          {#if activeTopic.links?.length}
            <div class="periodic-guide-links">
              <span>Fuentes y ampliación:</span>
              {#each activeTopic.links as link}<a href={link.url} target="_blank" rel="noreferrer">{link.label}</a>{/each}
            </div>
          {/if}
        </section>
      </div>
    </div>
  </div>
{/if}
