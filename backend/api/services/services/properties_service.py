#==============================#
#      PROPERTIES SERVICES     #
#==============================#
def parse_properties(server_id):
    server_path = "data/servers/" + server_id + "/server.properties"

    with open(server_path, "r") as file:
        content = file.read()

        properties = {}

        for line in content.splitlines():
            if "=" in line:
                setting, value = line.split("=", 1)

                properties[setting] = value

        return properties


def write_properties(server_id, new_properties):
    server_path = "data/servers/" + server_id + "/server.properties"

    with open(server_path, "r") as file:
        file_content = file.read() 

    lines = []
    found_properties = set()

    for line_index, line in enumerate(file_content.splitlines()):
        lines.append(line)

        if "=" in line:
            property_name, old_value = line.split("=", 1)

            found_properties.add(property_name)

            if property_name in new_properties:
                new_value = new_properties[property_name]
                if new_value != old_value:
                    lines[line_index] = (property_name + "=" + new_value)
                    
    for updated_property, new_value in new_properties.items(): 
        if updated_property not in found_properties:
            lines.append(updated_property + "=" + new_value)

    updated_content = "\n".join(lines)

    with open(server_path, "w") as file:
        file.write(updated_content)