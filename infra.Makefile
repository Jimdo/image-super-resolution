TERRAFORM                                   = ./terraform

terraform:
	@echo downloading terraform...
	@curl -sSLfo ./terraform.zip "https://releases.hashicorp.com/terraform/1.0.5/terraform_1.0.5_$(shell uname -s|tr A-Z a-z)_amd64.zip"
	@unzip -qq terraform.zip
	@rm -f terraform.zip
	@echo 'done'

infrastructure-plan: terraform
	cd infrastructure && ../$(TERRAFORM) init -input=false \
	&& ../$(TERRAFORM) plan -input=false

infrastructure-apply: terraform
	cd infrastructure && ../$(TERRAFORM) init -input=false \
	&& ../$(TERRAFORM) apply -input=false -auto-approve=true