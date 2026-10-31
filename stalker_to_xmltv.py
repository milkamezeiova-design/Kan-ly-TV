import json
import xml.etree.ElementTree as ET
from datetime import datetime
import os

def stalker_to_xmltv(input_json_path, output_xml_path):
    if not os.path.exists(input_json_path):
        print(f"Chyba: Vstupný súbor '{input_json_path}' neexistuje.")
        return
        
    try:
        with open(input_json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Chyba pri načítaní JSON: {e}")
        return

    # Stalker API zvyčajne balí dáta do objektu pod kľúč 'js'
    epg_list = data.get('js', [])
    if isinstance(epg_list, dict):
        # Niekedy je to slovník, kde kľúče sú ID kanálov alebo časy
        epg_list = epg_list.get('data', []) or list(epg_list.values())
    
    if not isinstance(epg_list, list):
        print("Chyba: Neočakávaný formát dát v JSON (očakáva sa zoznam programov).")
        return

    # Vytvorenie koreňového elementu XMLTV (<tv>)
    tv = ET.Element('tv', {
        'generator-info-name': 'Stalker to XMLTV Converter',
        'generator-info-url': 'http://localhost'
    })

    channels_added = set()

    # Pomocná funkcia na formátovanie času do XMLTV (YYYYMMDDhhmmss +0000)
    def format_time(time_str_or_ts):
        try:
            # Ak je to timestamp (sekundy)
            ts = float(time_str_or_ts)
            dt = datetime.fromtimestamp(ts)
            return dt.strftime('%Y%m%d%H%M%S +0100')
        except ValueError:
            # Ak je to string formát '2026-10-31 12:00:00'
            for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M'):
                try:
                    dt = datetime.strptime(str(time_str_or_ts), fmt)
                    return dt.strftime('%Y%m%d%H%M%S +0100')
                except ValueError:
                    continue
        return None

    # Prechod programami a plnenie XML
    for item in epg_list:
        if not isinstance(item, dict):
            continue
            
        ch_id = str(item.get('ch_id', item.get('channel_id', 'unknown')))
        ch_name = item.get('ch_name', item.get('channel_name', f'Channel {ch_id}'))
        
        # Pridanie kanálu do zoznamu <channel>, ak ešte nebol pridaný
        if ch_id not in channels_added and ch_id != 'unknown':
            channel_el = ET.SubElement(tv, 'channel', {'id': ch_id})
            display_name = ET.SubElement(channel_el, 'display-name', {'lang': 'sk'})
            display_name.text = ch_name
            channels_added.add(ch_id)

        # Časové údaje
        start_raw = item.get('start', item.get('time', item.get('start_time')))
        end_raw = item.get('end', item.get('time_to', item.get('end_time')))
        title_text = item.get('name', item.get('title', 'Neznámy program'))
        descr_text = item.get('descr', item.get('description', ''))

        start_formatted = format_time(start_raw) if start_raw else None
        end_formatted = format_time(end_raw) if end_raw else None

        if start_formatted and end_formatted:
            programme_el = ET.SubElement(tv, 'programme', {
                'start': start_formatted,
                'stop': end_formatted,
                'channel': ch_id
            })
            title_el = ET.SubElement(programme_el, 'title', {'lang': 'sk'})
            title_el.text = title_text
            
            if descr_text:
                descr_el = ET.SubElement(programme_el, 'desc', {'lang': 'sk'})
                descr_el.text = descr_text

    # Uloženie do XML súboru
    try:
        tree = ET.ElementTree(tv)
        ET.indent(tree, space="  ", level=0) # Pekné formátovanie (Python 3.9+)
        tree.write(output_xml_path, encoding='utf-8', xml_declaration=True)
        print(f"Úspešne skonvertované! XMLTV súbor bol uložený do: {output_xml_path}")
    except Exception as e:
        print(f"Chyba pri zápise XML: {e}")

if __name__ == '__main__':
    # Predvolené názvy súborov
    stalker_to_xmltv('epg_data.json', 'epg.xml')
