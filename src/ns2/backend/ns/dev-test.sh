rm ns
go build .
echo "DEV_TEST.sh: built"
sudo cp ns /usr/bin/ns
echo "DEV_TEST.sh: copied for global use"

sudo cp ~/Projects/ns-admin/configs/com.novus.ns.conf /usr/share/dbus-1/system.d/com.novus.ns.conf
sudo cp ~/Projects/ns-admin/configs/com.novus.ns.policy /usr/share/polkit-1/actions/com.novus.ns.policy

sudo cp ~/Projects/ns-admin/configs/ns-admin.rules /etc/polkit-1/rules.d/ns-admin.rules
sudo cp ~/Projects/ns-admin/configs/10-firewalld.rules /etc/polkit-1/rules.d/10-firewalld.rules
sudo cp ~/Projects/ns-admin/configs/10-systemd1.rules /etc/polkit-1/rules.d/10-systemd1.rules
sudo cp ~/Projects/ns-admin/configs/10-nm.rules /etc/polkit-1/rules.d/10-nm.rules

echo "DEV_TEST.sh: copied policy and ns.conf"

echo "DEV_TEST.sh: Starting dbus server..."
sudo ns dbus export

