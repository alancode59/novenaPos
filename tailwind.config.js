/* Sistema visual de posNovena. Marca: crema #EFE5D0, teal #1E5048, bermellon #D8452C.
   REGLA DEL ROJO: `accent` es solo decorativo; error usa `status.danger`. */

// Paleta cruda: en las plantillas usar los tokens semanticos, no estos nombres.
const palette = {
  // Crema de marca y neutros calidos (fondo, superficies, bordes)
  cream50: "#FDFBF6",
  cream100: "#FAF6EC", // superficie base de toda la app
  cream150: "#F1ECDF", // superficie "hundida" (inputs, wells)
  cream200: "#EFE5D0", // EXACTO del logo
  cream300: "#E4DCC8", // borde sutil / decorativo

  // Verde azulado de marca (acciones primarias, paneles de marca)
  teal50: "#EAF3F1",
  teal500: "#2B7A6D", // anillo de foco accesible
  teal600: "#1E5048", // EXACTO del logo -> interactive.primary
  teal700: "#173F39", // hover
  teal900: "#0F2B26", // active / pressed

  // Bermellon de marca (SOLO relleno/acento no interactivo, ver regla del rojo)
  vermillion100: "#F6DCD4",
  vermillion500: "#D8452C", // EXACTO del logo
  vermillion700: "#A22F1C", // unica variante de bermellon apta como TEXTO (AA)

  // Rojo de error/peligro, deliberadamente distinto del bermellon de marca
  danger100: "#FBE4E6",
  danger500: "#B3122E",
  danger600: "#8F0E24", // hover
  danger700: "#7A1120", // texto sobre danger-100 / active

  // Texto y bordes neutros (calidos, no gris frio, para que convivan con la crema)
  ink900: "#1F2A27", // texto principal
  ink700: "#4B5754", // texto secundario
  ink600: "#5A6763", // texto muted (aun AA en texto normal)
  sand500: "#9C8C68", // borde "fuerte" (inputs, cumple 3:1 sobre superficie base y blanco)
  sand700: "#8B7A57", // borde fuerte en estado hover/activo

  // Estados semanticos (alertas Y tablero de cocina comparten estas 4 familias)
  blue100: "#DBEAFE",
  blue600: "#2563EB",
  blue900: "#1E3A8A",

  amber100: "#FEF3C7",
  amber600: "#B45309",
  amber900: "#78350F",

  green100: "#DCFCE7",
  green700: "#15803D",
  green900: "#14532D",

  zinc200: "#E4E4E7",
  zinc600: "#52525B",
  zinc800: "#27272A",
};

module.exports = {
  content: ["./app/templates/**/*.html", "./app/static/js/**/*.js"],
  theme: {
    extend: {
      colors: {
        // Swatches exactos de marca (uso documental / logo / franjas de marca)
        brand: {
          cream: palette.cream200,
          teal: palette.teal600,
          vermillion: palette.vermillion500,
        },

        // Superficies (fondos de pantalla, tarjetas, paneles)
        surface: {
          base: palette.cream100, // fondo de pantalla. Texto ink-900 -> 13.7:1
          raised: "#FFFFFF", // tarjetas, modales, inputs. Texto ink-900 -> 14.8:1
          sunken: palette.cream150, // wells, filas alternas, inputs deshabilitados
          brand: palette.teal600, // paneles de marca (login, topbar). Texto inverse -> 8.6:1
          brandDark: palette.teal900, // hover/pressed sobre superficie de marca. Texto inverse -> 11.9:1
          disabled: palette.cream150,
        },

        // Texto
        text: {
          primary: palette.ink900, // sobre surface.base 13.7:1 / sobre white 14.8:1
          secondary: palette.ink700, // sobre surface.base 7.0:1 / sobre white 7.5:1
          muted: palette.ink600, // sobre surface.base 5.5:1 / sobre white 5.9:1 (texto normal OK)
          inverse: palette.cream50, // texto claro sobre fondos oscuros (teal). 8.6:1 / 11.9:1
          brand: palette.teal600, // titulos/enlaces sobre superficie clara. 8.5:1
          disabled: palette.sand500,
        },

        // Bordes
        border: {
          subtle: palette.cream300, // divisores decorativos, no es el unico indicador de un control
          DEFAULT: "#D6CBB0", // borde general de tarjetas
          strong: palette.sand500, // borde real de inputs/controles: 3.1:1 (base) / 3.3:1 (white), cumple 3:1 UI
          focus: palette.teal500, // anillo de foco: 4.7:1 sobre surface.base
          danger: palette.danger500, // borde de input en estado de error
        },

        // Acciones (botones, enlaces con apariencia de boton)
        interactive: {
          primary: {
            DEFAULT: palette.teal600, // texto inverse 8.6:1
            hover: palette.teal700, // texto inverse 11.0:1
            active: palette.teal900,
            text: palette.cream50,
          },
          secondary: {
            DEFAULT: "#FFFFFF",
            hover: palette.teal50,
            border: palette.teal600,
            text: palette.teal600, // 9.2:1 sobre white
          },
          danger: {
            // Rojo de ERROR/PELIGRO, deliberadamente distinto de accent (bermellon de marca).
            DEFAULT: palette.danger500, // texto blanco 6.9:1
            hover: palette.danger600, // texto blanco 9.3:1
            active: palette.danger700,
            text: "#FFFFFF",
          },
          disabled: {
            surface: palette.cream150,
            text: palette.sand500,
          },
        },

        // Solo decorativo: como texto no pasa AA (4.1:1), usar accent.dark.
        accent: {
          DEFAULT: palette.vermillion500,
          soft: palette.vermillion100,
          dark: palette.vermillion700, // unica variante apta para texto: 6.6:1 sobre surface.base
        },

        // Estados de alertas y KDS. Siempre con icono + etiqueta, no solo color.
        status: {
          info: { DEFAULT: palette.blue600, soft: palette.blue100, text: palette.blue900 },
          warning: { DEFAULT: palette.amber600, soft: palette.amber100, text: palette.amber900 },
          success: { DEFAULT: palette.green700, soft: palette.green100, text: palette.green900 },
          danger: { DEFAULT: palette.danger500, soft: palette.danger100, text: palette.danger700 },
          neutral: { DEFAULT: palette.zinc600, soft: palette.zinc200, text: palette.zinc800 },
        },

        // Alias de `status` para el KDS: new/preparing/ready/delivered.
        order: {
          new: { DEFAULT: palette.blue600, soft: palette.blue100, text: palette.blue900 },
          preparing: { DEFAULT: palette.amber600, soft: palette.amber100, text: palette.amber900 },
          ready: { DEFAULT: palette.green700, soft: palette.green100, text: palette.green900 },
          delivered: { DEFAULT: palette.zinc600, soft: palette.zinc200, text: palette.zinc800 },
        },
      },

      // Fredoka ecoa el logotipo; Inter para texto de interfaz.
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
        display: ["Fredoka", "ui-rounded", "ui-sans-serif", "system-ui", "sans-serif"],
      },

      // Escala para tablet: base grande y tamanos display para leer a distancia.
      fontSize: {
        xs: ["0.75rem", { lineHeight: "1rem" }], // metadatos, timestamps
        sm: ["0.875rem", { lineHeight: "1.25rem" }], // texto auxiliar
        base: ["1rem", { lineHeight: "1.5rem" }], // cuerpo por defecto
        lg: ["1.125rem", { lineHeight: "1.75rem" }],
        xl: ["1.25rem", { lineHeight: "1.75rem" }],
        "2xl": ["1.5rem", { lineHeight: "2rem" }], // encabezados de seccion
        "3xl": ["1.875rem", { lineHeight: "2.25rem" }], // titulo de pantalla
        "4xl": ["2.25rem", { lineHeight: "2.5rem" }],
        "display-1": ["3rem", { lineHeight: "1.1", letterSpacing: "-0.01em" }], // numero de mesa / folio
        "display-2": ["3.75rem", { lineHeight: "1", letterSpacing: "-0.01em" }], // KDS: lo que se lee a un brazo de distancia
      },

      // Areas tactiles: 44px es el minimo WCAG 2.5.5, mas variantes grandes.
      minHeight: {
        touch: "2.75rem", // 44px: minimo absoluto para cualquier control tocable
        "touch-lg": "3.5rem", // 56px: botones de accion primaria
        "touch-xl": "4.5rem", // 72px: acciones criticas de una sola pantalla (ej. "Marcar lista")
      },
      minWidth: {
        touch: "2.75rem",
        "touch-lg": "3.5rem",
      },

      borderRadius: {
        control: "0.625rem", // botones, inputs
        card: "1rem", // tarjetas, paneles
        pill: "9999px", // badges de estado
      },

      boxShadow: {
        card: "0 1px 2px 0 rgba(31, 42, 39, 0.06), 0 1px 3px 0 rgba(31, 42, 39, 0.08)",
        "card-hover": "0 2px 4px 0 rgba(31, 42, 39, 0.08), 0 4px 8px 0 rgba(31, 42, 39, 0.10)",
      },
    },
  },
  plugins: [],
};
