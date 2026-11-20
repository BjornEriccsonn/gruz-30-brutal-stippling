#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GRUZ-30 Stippling — GIMP 3.x Python-Fu plug-in.

Adds editable GEGL filter stacks to the selected layer and creates a separate
stippling layer from a rendered copy of the selected layer.
"""

import sys
import gi
gi.require_version('Gimp', '3.0')
gi.require_version('GimpUi', '3.0')
gi.require_version('Gegl', '0.4')
gi.require_version('Babl', '0.1')
gi.require_version('Gtk', '3.0')
from gi.repository import Gimp, GimpUi, Gegl, Babl, GLib, Gtk

PLUGIN = 'python-fu-gruz30-stippling'

# =============================================================================
#  WARTOŚCI DOMYŚLNE DO OKIEN DIALOGOWYCH (Możesz tu zmienić startowe wartości)
# =============================================================================

DEFAULT_ENGRAVING = {
    'levels_low': 35.0,        # 0 - 255 (odcięcie brudów w cieniach)
    'levels_high': 220.0,      # 0 - 255 (czyszczenie tła do czystej bieli)
    'levels_gamma': 1.0,       # 0.2 - 3.0 (środek tonalny)
    'contrast': 1.6,           # 0.5 - 3.0 (kontrast ogólny)
    'unsharp_radius': 5.0,     # promień maski wyostrzającej w px
    'unsharp_amount': 4.0,     # agresywność wyostrzania (1.0 = łagodnie, 3.5+ = kosa)
}

DEFAULT_BODY = {
    'shadows': 60.0,           # 0 - 100 (wyciąganie cieni)
    'highlights': -10.0,       # -50 - 50 (gaszenie przepaleń)
    'levels_low': 5.0,
    'levels_high': 240.0,
    'levels_gamma': 1.4,
    'large_radius': 30.0,      # promień kontrastu lokalnego (mięśnie/bryła)
    'large_amount': 1.8,       # siła kontrastu lokalnego
    'detail_radius': 3.5,      # promień mikrodetalu (pory, rzęsy)
    'detail_amount': 3.0,      # siła mikrodetalu
}

DEFAULT_OLD = {
    'blur_radius': 0.8,        # promień rozmycia starego druku
}

DEFAULT_STIPPLING = {
    'factor': 2,               # wielkość punktu (px)
    'dither': 'floyd',         # 'floyd' lub 'ordered'
    'gamma': 1.40,             # gęstość punktów (im wyższa, tym jaśniej)
    'max_pixels': 35_000_000,
}

# =============================================================================
#  INTERFEJS GRAFICZNY (GTK3)
# =============================================================================

def _add_spin(grid, row, label_text, val, min_v, max_v, step, digits=1):
    lbl = Gtk.Label(label=label_text)
    lbl.set_xalign(0)
    grid.attach(lbl, 0, row, 1, 1)

    adj = Gtk.Adjustment(value=val, lower=min_v, upper=max_v, step_increment=step, page_increment=step*5)
    spin = Gtk.SpinButton(adjustment=adj, climb_rate=step, digits=digits)
    grid.attach(spin, 1, row, 1, 1)
    return spin


def choose_profile():
    d = Gtk.Dialog(title='GRUZ-30 — Przygotowanie warstwy pod kropkowanie', flags=Gtk.DialogFlags.MODAL)
    d.add_button('_Anuluj', Gtk.ResponseType.CANCEL)
    d.add_button('_Zastosuj filtry', Gtk.ResponseType.OK)
    d.set_default_size(520, 480)

    box = d.get_content_area()
    box.set_border_width(14)
    box.set_spacing(10)

    intro = Gtk.Label(
        label='Dostosuj filtry przygotowawcze. Filtry zostaną dodane do warstwy '
              'niedestrukcyjnie (będziesz mógł je potem poprawić na liście filtrów GIMP-a).'
    )
    intro.set_line_wrap(True)
    intro.set_xalign(0)
    box.pack_start(intro, False, False, 0)

    # Wybór profilu
    hbox_prof = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
    lbl_p = Gtk.Label(label='Główny profil bazowy:')
    profile_combo = Gtk.ComboBoxText()
    profile_combo.append('engraving', 'Rycina / Komiks (ostre, twarde krawędzie)')
    profile_combo.append('body', 'Ciało / Portret (rzeźbienie bryły + mikrodetal)')
    profile_combo.append('old', 'Stary druk / Gazeta (wygładzenie rastra)')
    profile_combo.set_active_id('engraving')
    hbox_prof.pack_start(lbl_p, False, False, 0)
    hbox_prof.pack_start(profile_combo, True, True, 0)
    box.pack_start(hbox_prof, False, False, 0)

    # Kontener na dynamiczne parametry
    stack = Gtk.Stack()
    stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)

    # --- ZAKŁADKA: RYCINA ---
    grid_eng = Gtk.Grid(column_spacing=12, row_spacing=8)
    grid_eng.set_border_width(8)
    e_low = _add_spin(grid_eng, 0, 'Czerń wejściowa (odetnij szary brud w cieniach 0-255):', DEFAULT_ENGRAVING['levels_low'], 0, 150, 1, 0)
    e_high = _add_spin(grid_eng, 1, 'Biel wejściowa (wyczyść tło z kropek 0-255):', DEFAULT_ENGRAVING['levels_high'], 120, 255, 1, 0)
    e_gamma = _add_spin(grid_eng, 2, 'Gamma poziomów (środek tonalny):', DEFAULT_ENGRAVING['levels_gamma'], 0.2, 3.0, 0.05, 2)
    e_cont = _add_spin(grid_eng, 3, 'Kontrast ogólny:', DEFAULT_ENGRAVING['contrast'], 0.5, 3.5, 0.1, 2)
    e_rad = _add_spin(grid_eng, 4, 'Promień maski wyostrzającej (px):', DEFAULT_ENGRAVING['unsharp_radius'], 0.5, 30.0, 0.5, 1)
    e_amount = _add_spin(grid_eng, 5, 'SIŁA WYOSTRZANIA (agresywność krawędzi):', DEFAULT_ENGRAVING['unsharp_amount'], 0.5, 10.0, 0.2, 1)
    stack.add_named(grid_eng, 'engraving')

    # --- ZAKŁADKA: CIAŁO ---
    grid_body = Gtk.Grid(column_spacing=12, row_spacing=8)
    grid_body.set_border_width(8)
    b_shd = _add_spin(grid_body, 0, 'Rozjaśnienie głębokich cieni (0-100):', DEFAULT_BODY['shadows'], 0, 100, 5, 0)
    b_hl = _add_spin(grid_body, 1, 'Przygaszenie przepaleń (-50 do 50):', DEFAULT_BODY['highlights'], -50, 50, 5, 0)
    b_gamma = _add_spin(grid_body, 2, 'Korekta gammy skóry:', DEFAULT_BODY['levels_gamma'], 0.5, 2.5, 0.05, 2)
    b_lrad = _add_spin(grid_body, 3, 'Kontrast bryły (duży promień px):', DEFAULT_BODY['large_radius'], 5.0, 80.0, 5.0, 0)
    b_lamt = _add_spin(grid_body, 4, 'Siła uwypuklenia bryły/mięśni:', DEFAULT_BODY['large_amount'], 0.2, 5.0, 0.1, 1)
    b_drad = _add_spin(grid_body, 5, 'Wyostrzenie detali (mały promień px):', DEFAULT_BODY['detail_radius'], 0.5, 10.0, 0.5, 1)
    b_damt = _add_spin(grid_body, 6, 'Siła mikrodetali (pory, oczy, kontur):', DEFAULT_BODY['detail_amount'], 0.5, 8.0, 0.2, 1)
    stack.add_named(grid_body, 'body')

    # --- ZAKŁADKA: STARY DRUK ---
    grid_old = Gtk.Grid(column_spacing=12, row_spacing=8)
    grid_old.set_border_width(8)
    o_blur = _add_spin(grid_old, 0, 'Zmiękczenie starego druku / mory (promień px):', DEFAULT_OLD['blur_radius'], 0.2, 5.0, 0.1, 2)
    stack.add_named(grid_old, 'old')

    box.pack_start(stack, True, True, 0)

    def on_profile_change(combo):
        stack.set_visible_child_name(combo.get_active_id())

    profile_combo.connect('changed', on_profile_change)

    d.show_all()
    response = d.run()

    result = None
    if response == Gtk.ResponseType.OK:
        prof = profile_combo.get_active_id()
        if prof == 'engraving':
            result = {
                'profile': 'engraving',
                'levels_low': e_low.get_value() / 255.0,
                'levels_high': e_high.get_value() / 255.0,
                'levels_gamma': e_gamma.get_value(),
                'contrast': e_cont.get_value(),
                'unsharp_radius': e_rad.get_value(),
                'unsharp_amount': e_amount.get_value()
            }
        elif prof == 'body':
            result = {
                'profile': 'body',
                'shadows': b_shd.get_value(),
                'highlights': b_hl.get_value(),
                'levels_low': DEFAULT_BODY['levels_low'] / 255.0,
                'levels_high': DEFAULT_BODY['levels_high'] / 255.0,
                'levels_gamma': b_gamma.get_value(),
                'large_radius': b_lrad.get_value(),
                'large_amount': b_lamt.get_value(),
                'detail_radius': b_drad.get_value(),
                'detail_amount': b_damt.get_value()
            }
        elif prof == 'old':
            result = {
                'profile': 'old',
                'blur_radius': o_blur.get_value()
            }

    d.destroy()
    return result


def choose_stippling():
    d = Gtk.Dialog(title='GRUZ-30 — Rasteryzacja (Stippling)', flags=Gtk.DialogFlags.MODAL)
    d.add_button('_Anuluj', Gtk.ResponseType.CANCEL)
    d.add_button('_Wykonaj punkty', Gtk.ResponseType.OK)
    d.set_default_size(480, 320)

    box = d.get_content_area()
    box.set_border_width(14)
    box.set_spacing(10)

    intro = Gtk.Label(label='Generuje nową warstwę z czarno-białym rastrem kropkowym. Oryginał pozostaje bez zmian.')
    intro.set_line_wrap(True)
    intro.set_xalign(0)
    box.pack_start(intro, False, False, 0)

    grid = Gtk.Grid(column_spacing=12, row_spacing=10)

    # 1. Wielkość punktu
    dots = Gtk.ComboBoxText()
    dots.append('1', '1 × 1 px — natywny piksel (bardzo gęsty)')
    dots.append('2', '2 × 2 px — standard gazetowy (rekomendowany)')
    dots.append('3', '3 × 3 px — raster komiksowy / zin')
    dots.append('4', '4 × 4 px — styl retro')
    dots.append('6', '6 × 6 px — gruby raster')
    dots.append('8', '8 × 8 px — wyraźny raster pikselowy')
    dots.append('12', '12 × 12 px — bardzo gruby raster / plakat')
    dots.append('16', '16 × 16 px — ekstremalnie gruby raster')
    dots.set_active_id(str(DEFAULT_STIPPLING['factor']))
    _add_label = lambda txt, r: grid.attach(Gtk.Label(label=txt, xalign=0), 0, r, 1, 1)
    _add_label('Wielkość pojedynczej kropki:', 0)
    grid.attach(dots, 1, 0, 1, 1)

    # 2. Dithering
    dith = Gtk.ComboBoxText()
    dith.append('floyd', 'Floyd–Steinberg (organiczny, styl rapidografu)')
    dith.append('ordered', 'Bayer 8×8 (regularny, geometryczny raster)')
    dith.set_active_id(DEFAULT_STIPPLING['dither'])
    _add_label('Wzór ułożenia punktów:', 1)
    grid.attach(dith, 1, 1, 1, 1)

    # 3. Gamma
    gamma = _add_spin(grid, 2, 'Korekta gęstości (Gamma stipplingu):', DEFAULT_STIPPLING['gamma'], 0.5, 2.5, 0.05, 2)

    box.pack_start(grid, True, True, 0)

    tip = Gtk.Label(
        label='Porada do Gammy:\n'
              '• Jeśli po kropkowaniu obraz jest ZA CIEMNY (zalany czernią) -> zwiększ Gammę (np. 1.6 - 1.8).\n'
              '• Jeśli obraz jest ZA BLADY (za mało kropek w cieniach) -> zmniejsz Gammę (np. 1.1 - 1.25).'
    )
    tip.set_line_wrap(True)
    tip.set_xalign(0)
    box.pack_start(tip, False, False, 0)

    d.show_all()
    response = d.run()
    result = None
    if response == Gtk.ResponseType.OK:
        result = {
            'factor': int(dots.get_active_id()),
            'dither': dith.get_active_id(),
            'gamma': gamma.get_value()
        }
    d.destroy()
    return result

# =============================================================================
#  FILTRY I PRZETWARZANIE
# =============================================================================

def _append_filter(layer, operation, label, properties):
    try:
        filt = Gimp.DrawableFilter.new(layer, operation, label)
    except Exception as e:
        raise RuntimeError('GIMP odrzucił filtr %s: %s' % (operation, e)) from e
    if filt is None:
        raise RuntimeError('GIMP odrzucił filtr %s' % operation)
    config = filt.get_config()
    for key, value in properties.items():
        config.set_property(key, value)
    filt.update()
    layer.append_filter(filt)


def _apply_chosen_profile(layer, opts):
    prof = opts['profile']

    # Podstawa: konwersja do luminancji
    _append_filter(layer, 'gimp:desaturate', 'GRUZ-30 — luminancja', {
        'mode': Gimp.DesaturateMode.LUMINANCE
    })

    if prof == 'engraving':
        _append_filter(layer, 'gimp:levels', 'GRUZ-30 — odcięcie poziomów', {
            'channel': Gimp.HistogramChannel.VALUE,
            'low-input': opts['levels_low'],
            'high-input': opts['levels_high'],
            'gamma': opts['levels_gamma'],
            'low-output': 0.0,
            'high-output': 1.0
        })
        _append_filter(layer, 'gegl:brightness-contrast', 'GRUZ-30 — kontrast', {
            'brightness': 0.0,
            'contrast': opts['contrast']
        })
        _append_filter(layer, 'gegl:unsharp-mask', 'GRUZ-30 — ostre krawędzie', {
            'std-dev': opts['unsharp_radius'],
            'scale': opts['unsharp_amount'],
            'threshold': 0.0
        })

    elif prof == 'body':
        _append_filter(layer, 'gegl:shadows-highlights', 'GRUZ-30 — cienie i światła', {
            'shadows': opts['shadows'],
            'highlights': opts['highlights']
        })
        _append_filter(layer, 'gimp:levels', 'GRUZ-30 — poziomy i gamma', {
            'channel': Gimp.HistogramChannel.VALUE,
            'low-input': opts['levels_low'],
            'high-input': opts['levels_high'],
            'gamma': opts['levels_gamma'],
            'low-output': 0.0,
            'high-output': 1.0
        })
        _append_filter(layer, 'gegl:unsharp-mask', 'GRUZ-30 — bryła (duży promień)', {
            'std-dev': opts['large_radius'],
            'scale': opts['large_amount'],
            'threshold': 0.0
        })
        _append_filter(layer, 'gegl:unsharp-mask', 'GRUZ-30 — detale (mały promień)', {
            'std-dev': opts['detail_radius'],
            'scale': opts['detail_amount'],
            'threshold': 0.0
        })

    elif prof == 'old':
        _append_filter(layer, 'gegl:gaussian-blur', 'GRUZ-30 — zmiękczenie mory', {
            'std-dev-x': opts['blur_radius'],
            'std-dev-y': opts['blur_radius'],
            'abyss-policy': 'clamp'
        })


def clamp(v, lo=0.0, hi=255.0):
    return max(lo, min(hi, v))


def _downsample_average(src, width, height, factor):
    sw = max(1, (width + factor - 1) // factor)
    sh = max(1, (height + factor - 1) // factor)
    gray = [255.0] * (sw * sh)
    alpha = [255] * (sw * sh)
    for y in range(sh):
        y0, y1 = y * factor, min(height, (y + 1) * factor)
        for x in range(sw):
            x0, x1 = x * factor, min(width, (x + 1) * factor)
            total = asum = count = 0
            for yy in range(y0, y1):
                base = yy * width * 4
                for xx in range(x0, x1):
                    i = base + xx * 4
                    total += 0.2126 * src[i] + 0.7152 * src[i + 1] + 0.0722 * src[i + 2]
                    asum += src[i + 3]
                    count += 1
            j = y * sw + x
            gray[j] = total / max(1, count)
            alpha[j] = int(asum / max(1, count))
    return sw, sh, gray, alpha


_BAYER8 = [
    [0,  48, 12, 60, 3,  51, 15, 63],
    [32, 16, 44, 28, 35, 19, 47, 31],
    [8,  56,  4, 52, 11, 59,  7, 55],
    [40, 24, 36, 20, 43, 27, 39, 23],
    [2,  50, 14, 62, 1,  49, 13, 61],
    [34, 18, 46, 30, 33, 17, 45, 29],
    [10, 58,  6, 54, 9,  57,  5, 53],
    [42, 26, 38, 22, 41, 25, 37, 21]
]


def _floyd(gray, width, height, gamma):
    work = [255.0 * ((clamp(v) / 255.0) ** (1.0 / gamma)) for v in gray]
    out = bytearray(len(work))
    for y in range(height):
        for x in range(width):
            i = y * width + x
            old = clamp(work[i])
            new = 255 if old >= 127.5 else 0
            out[i] = new
            err = old - new
            if x + 1 < width:
                work[i + 1] += err * 7.0 / 16.0
            if y + 1 < height:
                if x > 0:
                    work[i + width - 1] += err * 3.0 / 16.0
                work[i + width] += err * 5.0 / 16.0
                if x + 1 < width:
                    work[i + width + 1] += err / 16.0
    return out


def _ordered(gray, width, height, gamma):
    out = bytearray(len(gray))
    for y in range(height):
        for x in range(width):
            i = y * width + x
            v = 255.0 * ((clamp(gray[i]) / 255.0) ** (1.0 / gamma))
            threshold = (_BAYER8[y % 8][x % 8] + 0.5) * 4.0
            out[i] = 255 if v >= threshold else 0
    return out


def _make_stipple_layer(image, source, opts):
    width, height = source.get_width(), source.get_height()
    if width * height > DEFAULT_STIPPLING['max_pixels']:
        raise RuntimeError('Warstwa przekracza limit bezpieczeństwa pikseli. Zmniejsz rozmiar obrazu.')

    rendered = source.copy()
    image.insert_layer(rendered, source.get_parent(), image.get_item_position(source))
    rendered.set_name('GRUZ-30 — kopia do rasteryzacji')

    if not rendered.has_alpha():
        rendered.add_alpha()

    rendered.merge_filters()

    rect = Gegl.Rectangle.new(0, 0, width, height)
    buf = rendered.get_buffer()
    raw = buf.get(rect, 1.0, "R'G'B'A u8", Gegl.AbyssPolicy.CLAMP)

    factor = opts['factor']
    sw, sh, gray, alpha = _downsample_average(raw, width, height, factor)
    mono = _ordered(gray, sw, sh, opts['gamma']) if opts['dither'] == 'ordered' else _floyd(gray, sw, sh, opts['gamma'])

    output = bytearray(width * height * 4)
    target_row_len = width * 4

    for sy in range(sh):
        row_buf = bytearray()
        base_s = sy * sw
        for sx in range(sw):
            si = base_s + sx
            val = mono[si]
            px = bytes((val, val, val, alpha[si]))
            row_buf.extend(px * factor)

        row_slice = bytes(row_buf[:target_row_len])
        y_start = sy * factor
        y_end = min(height, (sy + 1) * factor)
        for y in range(y_start, y_end):
            dest_offset = y * target_row_len
            output[dest_offset : dest_offset + target_row_len] = row_slice

    rendered.set_name('GRUZ-30 — STIPPLING — %d px' % factor)
    shadow = rendered.get_shadow_buffer()
    shadow.set(rect, "R'G'B'A u8", bytes(output))
    shadow.flush()
    rendered.merge_shadow(True)
    rendered.update(0, 0, width, height)

# =============================================================================
#  PDB CALLBACKS
# =============================================================================

def _run_profile(proc, run_mode, image, drawables, config, data):
    if not drawables or not isinstance(drawables[0], Gimp.Layer):
        return proc.new_return_values(Gimp.PDBStatusType.CALLING_ERROR, GLib.Error('Zaznacz warstwę obrazu.'))
    layer = drawables[0]

    if run_mode == Gimp.RunMode.INTERACTIVE:
        GimpUi.init('gruz30_stippling')
        opts = choose_profile()
        if opts is None:
            return proc.new_return_values(Gimp.PDBStatusType.CANCEL, GLib.Error())
    else:
        opts = {
            'profile': 'engraving',
            'levels_low': DEFAULT_ENGRAVING['levels_low'] / 255.0,
            'levels_high': DEFAULT_ENGRAVING['levels_high'] / 255.0,
            'levels_gamma': DEFAULT_ENGRAVING['levels_gamma'],
            'contrast': DEFAULT_ENGRAVING['contrast'],
            'unsharp_radius': DEFAULT_ENGRAVING['unsharp_radius'],
            'unsharp_amount': DEFAULT_ENGRAVING['unsharp_amount']
        }

    try:
        image.undo_group_start()
        _apply_chosen_profile(layer, opts)
        image.undo_group_end()
        Gimp.displays_flush()
        return proc.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())
    except Exception as e:
        try:
            image.undo_group_end()
        except Exception:
            pass
        return proc.new_return_values(Gimp.PDBStatusType.EXECUTION_ERROR, GLib.Error('GRUZ-30: ' + str(e)))


def _run_stippling(proc, run_mode, image, drawables, config, data):
    if not drawables or not isinstance(drawables[0], Gimp.Layer):
        return proc.new_return_values(Gimp.PDBStatusType.CALLING_ERROR, GLib.Error('Zaznacz warstwę obrazu.'))
    source = drawables[0]

    if run_mode == Gimp.RunMode.INTERACTIVE:
        GimpUi.init('gruz30_stippling')
        opts = choose_stippling()
        if opts is None:
            return proc.new_return_values(Gimp.PDBStatusType.CANCEL, GLib.Error())
    else:
        opts = {
            'factor': DEFAULT_STIPPLING['factor'],
            'dither': DEFAULT_STIPPLING['dither'],
            'gamma': DEFAULT_STIPPLING['gamma']
        }

    try:
        Gegl.init(None)
        image.undo_group_start()
        _make_stipple_layer(image, source, opts)
        image.undo_group_end()
        Gimp.displays_flush()
        return proc.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())
    except Exception as e:
        try:
            image.undo_group_end()
        except Exception:
            pass
        return proc.new_return_values(Gimp.PDBStatusType.EXECUTION_ERROR, GLib.Error('GRUZ-30 Stippling: ' + str(e)))


class Gruz30Stippling(Gimp.PlugIn):
    def do_set_i18n(self, procname):
        return False

    def do_query_procedures(self):
        return [PLUGIN + '-prepare', PLUGIN + '-rasterize']

    def do_create_procedure(self, name):
        if name == PLUGIN + '-prepare':
            proc = Gimp.ImageProcedure.new(self, name, Gimp.PDBProcType.PLUGIN, _run_profile, None)
            proc.set_image_types('*')
            proc.set_sensitivity_mask(Gimp.ProcedureSensitivityMask.DRAWABLE)
            proc.set_menu_label('GRUZ-30 — 1. Przygotuj warstwę')
            proc.add_menu_path('<Image>/Filters/Artistic/GRUZ-30')
            proc.set_documentation(
                'Dodaje stos filtrów GRUZ-30 z podglądem parametrów',
                'Niedestrukcyjne przygotowanie kontrastu, poziomów i masek wyostrzających pod stippling.',
                name
            )
            proc.set_attribution('OpenAI', 'OpenAI', '2026')
            return proc
        if name == PLUGIN + '-rasterize':
            proc = Gimp.ImageProcedure.new(self, name, Gimp.PDBProcType.PLUGIN, _run_stippling, None)
            proc.set_image_types('*')
            proc.set_sensitivity_mask(Gimp.ProcedureSensitivityMask.DRAWABLE)
            proc.set_menu_label('GRUZ-30 — 2. Wykonaj stippling')
            proc.add_menu_path('<Image>/Filters/Artistic/GRUZ-30')
            proc.set_documentation(
                'Tworzy warstwę ze stipplingiem',
                'Rasteruje widoczny wynik zaznaczonej warstwy i jej filtrów na osobnej warstwie.',
                name
            )
            proc.set_attribution('OpenAI', 'OpenAI', '2026')
            return proc
        return None


Gimp.main(Gruz30Stippling.__gtype__, sys.argv)