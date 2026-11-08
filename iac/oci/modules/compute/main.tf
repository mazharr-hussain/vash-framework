terraform {
  required_providers {
    oci = {
      source = "oracle/oci"
      version = ">= 6.0"
    }
  }
}

resource "oci_core_instance" "runner" {
  compartment_id      = var.compartment_id
  availability_domain = var.availability_domain
  shape               = "VM.Standard.A1.Flex"
  display_name        = "vash-runner"

  shape_config {
    ocpus         = 2
    memory_in_gbs = 12
  }

  source_details {
    source_type = "image"
    source_id   = var.image_id
  }

  create_vnic_details {
    subnet_id = var.subnet_id
  }

  metadata = {
    ssh_authorized_keys = var.ssh_public_key
  }
}
