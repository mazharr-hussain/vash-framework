# VASH onboarding

One command in OCI Cloud Shell creates an Always Free Arm VM and installs VASH on it.

```bash
curl -fsSL https://raw.githubusercontent.com/mazharr-hussain/vash-framework/main/bootstrap/oci-cloudshell.sh | bash
```

What it does (`vash onboard oci`):

0. Asks whether to check the existing compartments, VCNs and subnets, and shows them in one table (S.No, type, name, state, the compartment or VCN each belongs to, public or not, OCID). It then asks whether to delete any: you give S.No or OCIDs, comma separated. For each choice it lists what would also be deleted (a VCN's subnets, gateways, route tables, lists) and what still uses it (IPs of VMs, databases or load balancers in a subnet, peering or DRG attachments, resources in a compartment); anything in use is blocked. Only the free ones are offered, with one last yes/no. Finally it offers a public subnet from the table for the VASH VM (Enter = create a new network).
1. Reads the tenancy and region from Cloud Shell, asks for the compartment name (default `vash`), and reuses it or, after a yes, creates it.
2. Checks the free A1 quota in each availability domain and keeps those with 2 cores and 12 GB free.
3. Picks the latest Ubuntu 24.04 Arm image, creates an SSH key if there is none, and opens SSH to this shell's IP only.
4. Asks once, then runs terraform on `iac/oci/environments/always-free`; on "Out of host capacity" it tries the next domain.
5. The VM installs on first boot: Python, git, terraform, VASH, Ollama with `qwen2.5-coder:7b`, and the GitHub Actions runner files.
6. Waits until the VM reports ready, then prints the SSH command.

Options (after `bash -s --`):

- `--runner-repo owner/name`: register the VM as a self-hosted runner. The token is asked at a prompt and sent over SSH stdin; it is never written to a file.
- `--ocpus 4 --memory 24`: a bigger VM (the whole free A1 allowance).
- `--admin-cidr x.x.x.x/32`: who may SSH in (only for the network VASH creates).
- `--subnet-id <ocid>`: use an existing public subnet instead of creating a network (for example when the free VCN limit is reached). It must allow SSH (TCP 22); VASH checks it and never changes it.
- `--compartment <name>`: the compartment to use. Without it, VASH asks for the name (Enter keeps `vash`); a compartment that does not exist is created only after a yes.
- `--yes`: do not ask before creating (the inventory and every delete are skipped).
- `--no-inventory`: skip step 0.
- `--down`: remove the VM and its network.

Running it again is safe: the terraform state lives in `~/.vash/oci`, the earlier domain and image are kept, and terraform only repairs what drifted.
