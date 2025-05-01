import xml.etree.ElementTree as ET
from xml.etree.ElementTree import Element, SubElement, tostring
import xml.dom.minidom
import json
import os

def parse_input_xml(file_path):
    tree = ET.parse(file_path)
    root = tree.getroot()

    classes = {}
    aggregations = []

    for elem in root:
        if elem.tag == 'Class':
            class_name = elem.get('name')
            attributes = []
            for attr in elem.findall('Attribute'):
                attributes.append({
                    'name': attr.get('name'),
                    'type': attr.get('type')
                })
            classes[class_name] = {
                'name': class_name,
                'isRoot': elem.get('isRoot') == 'true',
                'documentation': elem.get('documentation'),
                'attributes': attributes
            }
        elif elem.tag == 'Aggregation':
            aggregations.append({
                'source': elem.get('source'),
                'target': elem.get('target'),
                'sourceMultiplicity': elem.get('sourceMultiplicity'),
                'targetMultiplicity': elem.get('targetMultiplicity')
            })
    return classes, aggregations

def build_meta_json(classes, aggregations):
    class_meta = []
    for class_name in classes:
        class_info = classes[class_name]
        relevant_aggs = [agg for agg in aggregations if agg['source'] == class_name]
        min_val = '0'
        max_val = '1'
        if relevant_aggs:
            multiplicity = relevant_aggs[0]['sourceMultiplicity']
            if '..' in multiplicity:
                min_val, max_val = multiplicity.split('..')
            else:
                min_val = max_val = multiplicity
        else:
            if class_info['isRoot']:
                min_val = max_val = '1'

        parameters = []
        for attr in class_info['attributes']:
            parameters.append({
                'name': attr['name'],
                'type': attr['type']
            })
        for agg in aggregations:
            if agg['target'] == class_name:
                parameters.append({
                    'name': agg['source'],
                    'type': 'class'
                })

        meta_entry = {
            'class': class_name,
            'documentation': class_info['documentation'],
            'isRoot': class_info['isRoot'],
            'min': min_val,
            'max': max_val,
            'parameters': parameters
        }
        class_meta.append(meta_entry)
    
    class_order = ['MetricJob', 'CPLANE', 'MGMT', 'RU', 'HWE', 'COMM', 'BTS']
    sorted_class_meta = sorted(class_meta, key=lambda x: class_order.index(x['class']))
    return sorted_class_meta

def build_config_xml(classes, aggregations):
    def build_element(class_name, parent):
        class_info = classes[class_name]
        element = SubElement(parent, class_name)
        for attr in class_info['attributes']:
            attr_elem = SubElement(element, attr['name'])
            attr_elem.text = attr['type']
        for agg in aggregations:
            if agg['target'] == class_name:
                build_element(agg['source'], element)
        return element

    root_element = Element('BTS')
    build_element('BTS', root_element)
    return root_element

def main():
    os.makedirs('out', exist_ok=True)
    classes, aggregations = parse_input_xml('impulse_test_input.xml')

    meta_data = build_meta_json(classes, aggregations)
    with open('out/meta.json', 'w', encoding='utf-8') as f:
        json.dump(meta_data, f, indent=4, ensure_ascii=False)

    config_root = build_config_xml(classes, aggregations)
    rough_xml = tostring(config_root, 'utf-8')
    parsed_xml = xml.dom.minidom.parseString(rough_xml)
    pretty_xml = parsed_xml.toprettyxml(indent='    ')
    pretty_xml = '\n'.join([line for line in pretty_xml.split('\n') if line.strip()])
    with open('out/config.xml', 'w', encoding='utf-8') as f:
        f.write(pretty_xml)

if __name__ == '__main__':
    main()