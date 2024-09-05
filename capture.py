import pyshark
import csv
from datetime import datetime
import threading
import queue
import json
from flask import Flask, request, jsonify
import requests
from collections import defaultdict, deque

class TrafficMetrics:
    def __init__(self, window_size=10):
        self.window_size = window_size
        self.packets = deque()
        self.protocol_freq = defaultdict(int)
        self.lock = threading.Lock()

    def update(self, packet):
        with self.lock:
            current_time = datetime.fromtimestamp(float(packet.sniff_timestamp))
            self.packets.append((current_time, packet.highest_layer))
            
            # Define the list of specified protocols
            specified_protocols = {'ENIP', 'CIPCM', 'TCP', 'UDP', 'ICMPV6'}

            # Check if the packet's highest layer is in the specified protocols
            ptl = packet.highest_layer
            if ptl not in specified_protocols:
                ptl = 'other'

            # Update the protocol_freq dictionary
            self.protocol_freq[ptl] += 1

            # Remove packets that are older than the window size
            while self.packets and (current_time - self.packets[0][0]).total_seconds() > self.window_size:
                old_time, old_protocol = self.packets.popleft()
                
                # Check if the old_protocol is in the specified protocols
                if old_protocol not in specified_protocols:
                    old_protocol = 'other'
                
                # Update the protocol_freq dictionary
                self.protocol_freq[old_protocol] -= 1
                if self.protocol_freq[old_protocol] <= 0:
                    del self.protocol_freq[old_protocol]

    def get_metrics(self):
        with self.lock:
            # Define the list of specified protocols
            specified_protocols = {'ENIP', 'CIP', 'TCP', 'UDP', 'ICMP'}

            # Remove outdated packets before calculating metrics
            current_time = datetime.now()
            while self.packets and (current_time - self.packets[0][0]).total_seconds() > self.window_size:
                old_time, old_protocol = self.packets.popleft()
                
                # Check if the old_protocol is in the specified protocols
                if old_protocol not in specified_protocols:
                    old_protocol = 'other'
                
                # Update the protocol_freq dictionary
                self.protocol_freq[old_protocol] -= 1
                if self.protocol_freq[old_protocol] <= 0:
                    del self.protocol_freq[old_protocol]

            return {
                'packet_count': len(self.packets),
                'protocol_freq': dict(self.protocol_freq)
            }

class Packet:
    def __init__(self, timestamp, packet_data):
        self.timestamp = timestamp
        self.packet_data = packet_data

    def __lt__(self, other):
        return self.timestamp < other.timestamp

app = Flask(__name__)
packet_data_store = []

@app.route('/packets', methods=['POST'])
def receive_packets():
    global packet_data_store
    data = request.json
    packet_data_store.extend(data)
    print(f"Received {len(data)} packets. Total packets: {len(packet_data_store)}")
    return jsonify({"status": "success", "received": len(data)}), 200

@app.route('/packets', methods=['GET'])
def get_packets():
    return jsonify(packet_data_store)

@app.route('/metrics', methods=['GET'])
def get_metrics():
    return jsonify(traffic_metrics.get_metrics())

def run_flask_app():
    app.run(host='localhost', port=5000)

traffic_metrics = TrafficMetrics()

def capture_packets(interface, packet_queue, packet_count=None):
    capture = pyshark.LiveCapture(interface=interface)
    for pkt_count, packet in enumerate(capture.sniff_continuously(packet_count=99999999999999), 1):
        try:
            protocol = packet.highest_layer
            if 'IP' in packet:
                src_addr = packet.ip.src
                dst_addr = packet.ip.dst
            elif 'IPv6' in packet:
                src_addr = packet.ipv6.src
                dst_addr = packet.ipv6.dst
            else:
                src_addr = packet.layers[0].src
                dst_addr = packet.layers[0].dst
            length = len(packet)
            info = get_protocol_info(packet)
            timestamp = datetime.fromtimestamp(float(packet.sniff_timestamp))
            formatted_time = timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
            
            packet_data = {
                "interface": interface,
                "no": pkt_count,
                "time": formatted_time,
                "source": src_addr,
                "destination": dst_addr,
                "protocol": protocol,
                "length": length,
                "info": info
            }

            traffic_metrics.update(packet)
            
            packet_queue.put(Packet(timestamp, packet_data))
            print(f"Packet {pkt_count} from {interface}: {protocol}")
        except AttributeError as e:
            print(f"Error processing packet {pkt_count} from {interface}: {str(e)}")

def get_protocol_info(packet):
    highest_layer = packet.highest_layer
    if highest_layer == 'TCP':
        return f"{packet.tcp.srcport} → {packet.tcp.dstport} {packet.tcp.flags}"
    elif highest_layer == 'UDP':
        return f"{packet.udp.srcport} → {packet.udp.dstport}"
    elif highest_layer == 'ICMP':
        return f"Type: {packet.icmp.type}, Code: {packet.icmp.code}"
    elif highest_layer == 'DNS':
        return f"ID: {packet.dns.id} {packet.dns.qry_name}"
    elif 'ENIP' in packet:
        return f"Command: {packet.enip.command}"
    elif 'CIP' in packet:
        return f"Service: {packet.cip.service}"
    else:
        return getattr(packet, 'summary', highest_layer)

def write_to_csv_and_api(packet_queue, output_file, api_endpoint):
    with open(output_file, 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(["Interface", "No.", "Time", "Source", "Destination", "Protocol", "Length", "Info"])
        i = 0
        
        batch = []
        while True:
            try:
                packet_data = packet_queue.get(timeout=1).packet_data
                csvwriter.writerow([
                    packet_data["interface"],
                    packet_data["no"],
                    packet_data["time"],
                    packet_data["source"],
                    packet_data["destination"],
                    packet_data["protocol"],
                    packet_data["length"],
                    packet_data["info"]
                ])
                batch.append(packet_data)
                
                if len(batch) >= 10:  # Adjust batch size as needed
                    post_to_api(api_endpoint, batch)
                    batch = []
                
            except queue.Empty:
                if batch:
                    post_to_api(api_endpoint, batch)

                i += 1
                if i == 10:
                    break
            except TypeError:
                if batch:
                    post_to_api(api_endpoint, batch)

                i += 1
                if i == 10:
                    break
                

def post_to_api(api_endpoint, data):
    try:
        response = requests.post(api_endpoint, json=data)
        response.raise_for_status()
        print(f"Successfully posted {len(data)} packets to API")
    except requests.RequestException as e:
        print(f"Error posting to API: {str(e)}")

def capture_all_interfaces(interfaces, output_file, api_endpoint, packet_count=None):
    packet_queue = queue.PriorityQueue()
    threads = []

    for interface in interfaces:
        thread = threading.Thread(target=capture_packets, args=(interface, packet_queue, packet_count))
        thread.start()
        threads.append(thread)


    # Start a thread to write to CSV and post to API
    write_thread = threading.Thread(target=write_to_csv_and_api, args=(packet_queue, output_file, api_endpoint))
    write_thread.start()

    # Wait for all capture threads to finish
    for thread in threads:
        thread.join()

    # Signal the write thread to finish
    packet_queue.put(Packet(datetime.max, None))
    write_thread.join()

    print("Capture completed")

if __name__ == "__main__":
    interfaces = ['s1-eth1', 's1-eth2', 's1-eth3']  # Replace with your capture interfaces
    output_file = 'multi_interface_capture3.csv'
    api_endpoint = 'http://localhost:5000/packets'
    
    # Start the Flask app in a separate thread
    flask_thread = threading.Thread(target=run_flask_app)
    flask_thread.start()

    # Start packet capture
    capture_all_interfaces(interfaces, output_file, api_endpoint, packet_count=1000)  # Capture 1000 packets per interface

    print("All done")
    # Keep the main thread running to allow Flask to continue serving
    flask_thread.join()

    print("Exiting")