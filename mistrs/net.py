from ipaddress import IPv4Network

def subnet(network: str, cidr: int):
	# Takes a network and breaks it down into smaller subnets with CIDR as an integer. Returns an array with network strings
	Net_Array = []
	count = 0
	supernet = IPv4Network(network)
	print(f"Creating subnets from {network} as /{cidr}s")
	for n in supernet.subnets(new_prefix = cidr):
		count = count+1
		data = {
		"Seq": count,
		"Network": str(n),
		"First Host": str(n[1]),
		"Last Host": str(n[-2]),
		"Broadcast": str(n[-1])
		}
		Net_Array.append(data)
	print ("Created {} Subnets".format(count))
	return Net_Array