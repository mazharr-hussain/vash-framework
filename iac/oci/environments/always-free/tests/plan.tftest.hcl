# Offline plan checks (terraform test with a mocked oci provider: no cloud calls, no credentials).
# They catch module wiring errors, such as CD3 defaults that fail at plan time, before a live run.
mock_provider "oci" {}

variables {
  region              = "me-jeddah-1"
  compartment_id      = "ocid1.compartment.oc1..test"
  availability_domain = "test:ME-JEDDAH-1-AD-1"
  image_id            = "ocid1.image.oc1.me-jeddah-1.test"
  admin_cidr          = "198.51.100.1/32"
  ssh_public_key      = "ssh-rsa AAAA test"
  oci_auth            = "InstancePrincipal"
  cloud_init_script   = "vash-runner.sh"
  name_prefix         = "vash"
}

run "new_network_and_vm" {
  command = plan
  assert {
    condition     = length(module.vcn) == 1 && length(module.subnet) == 1
    error_message = "A run without subnet_id must create the network."
  }
}

run "existing_subnet_creates_no_network" {
  command = plan
  variables {
    subnet_id = "ocid1.subnet.oc1.me-jeddah-1.test"
  }
  assert {
    condition     = length(module.vcn) == 0 && length(module.subnet) == 0
    error_message = "A run with subnet_id must not create a network."
  }
}

run "with_free_database" {
  command = plan
  variables {
    create_database = true
  }
}

run "email_when_the_vm_is_made" {
  command = plan
  variables {
    notify_email = "owner@example.com"
  }
  assert {
    condition     = length(module.notification) == 1 && length(module.vm_created_event) == 1
    error_message = "An e-mail address must plan the topic and the event rule."
  }
}

run "no_email_by_default" {
  command = plan
  assert {
    condition     = length(module.notification) == 0 && length(module.vm_created_event) == 0
    error_message = "Without an e-mail address nothing is sent."
  }
}
