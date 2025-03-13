#!/usr/bin/env python3
from ruamel.yaml import YAML
import copy

def main():
    yaml = YAML()
    output_file = "subscribers.yaml"
    
    # Number of subscribers to create
    num_subscribers = 2048

    # Start IMSI at "20893" plus enough digits, e.g. 208930000000001
    # Adjust to match your desired numbering scheme
    imsi_start_int = 208930000000001

    # A basic template – modify any fields as needed
    subscriber_template = {
        "_id": "",
        "imsi": "",  # Filled in loop
        "subscribed_rau_tau_timer": 12,
        "network_access_mode": 0,
        "subscriber_status": 0,
        "access_restriction_data": 32,
        "slice": [
            {
                "sst": 1,
                "sd": "ffffff",            # <-- Updated to 0xffffff
                "default_indicator": True,
                "session": [
                    {
                        "name": "internet",
                        "type": 1,
                        "pcc_rule": [],
                        "ambr": {
                            "uplink": {"value": 1, "unit": 3},
                            "downlink": {"value": 1, "unit": 3}
                        },
                        "qos": {
                            "index": 9,
                            "arp": {
                                "priority_level": 8,
                                "pre_emption_capability": 1,
                                "pre_emption_vulnerability": 1
                            }
                        }
                    }
                ]
            }
        ],
        "ambr": {
            "uplink": {"value": 1, "unit": 3},
            "downlink": {"value": 1, "unit": 3}
        },
        "security": {
            "k": "465B5CE8B199B49FAA5F0A2EE238A6BC",
            "amf": "8000",
            "op": "",
            "opc": "E8ED289DEBA952E4283B54E88E6183CA"
        },
        "schema_version": 1,
        "__v": 0
    }

    all_subscribers = {}
    
    for i in range(num_subscribers):
        # Generate a new subscriber dict (deep copy so we don't mutate the original)
        subscriber_data = copy.deepcopy(subscriber_template)
        
        # Compute this subscriber's IMSI
        # e.g. 208930000000001, 208930000000002, ...
        imsi_int = imsi_start_int + i
        subscriber_data["imsi"] = str(imsi_int)

        # Each subscriber key can be subscriber_1, subscriber_2, etc.
        subscriber_key = f"subscriber_{i + 1}"
        all_subscribers[subscriber_key] = subscriber_data

    # Dump to YAML
    with open(output_file, "w") as f:
        yaml.dump(all_subscribers, f)

    print(f"Generated {num_subscribers} subscribers in {output_file}")

if __name__ == "__main__":
    main()
