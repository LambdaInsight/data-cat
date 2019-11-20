# -*- mode: ruby -*-
# vi: set ft=ruby :

ssh_key = File.open(File.join(Dir.home, '.ssh/id_rsa.pub'), "rb").read

unix_user = 'centos'
unix_group = 'centos'

$script = <<SCRIPT
SYSTEM_USER=$(grep "^#{unix_user}" /etc/passwd)
if [ -z "$SYSTEM_USER" ]; then
    echo "#{unix_user} user does not exists"
    adduser "#{unix_user}" -m
    mkdir -p "/home/#{unix_user}/.ssh/"
    echo "#{ssh_key}" >> "/home/#{unix_user}/.ssh/authorized_keys"
    chmod 700 "/home/#{unix_user}/.ssh/"
    chmod 600 "/home/#{unix_user}/.ssh/authorized_keys"
    chown -R "#{unix_user}":"#{unix_group}" "/home/#{unix_user}/.ssh"
    echo "#{unix_user} ALL=(ALL)       NOPASSWD:       ALL" >> /etc/sudoers
fi
SCRIPT

Vagrant.configure("2") do |config|
  #This executes the above
  config.vm.provision "shell", inline: $script

  config.vm.synced_folder ".", "/vagrant", disabled: true

  config.vm.provider "virtualbox" do |vb|
    vb.gui = false
    vb.customize ['modifyvm', :id, "--chipset", "ich9"]
    vb.memory = 1024
    vb.cpus = 2
  end

  config.vm.define "dd" do |node|
    node.vm.box = "centos/7"
    node.vm.host_name = 'd' + '.lambdainsight.local'
    node.vm.network 'private_network', ip: '10.20.30.42'
  end

end
