
sudo apt install libssl-dev automake autoconf libncurses5-dev gcc

wget https://github.com/erlang/otp/releases/download/OTP-24.0.5/otp_src_24.0.5.tar.gz
tar -zxf otp_src_24.0.5.tar.gz
cd otp_src_24.0.5/
export ERL_TOP=`pwd`
export LANG=C
./configure --prefix /opt/erlang/24.0.5
make
make install


cd /usr/bin
sudo ln -s /opt/erlang/24.0.5/bin/erl .
sudo ln -s /opt/erlang/24.0.5/bin/escript .
sudo ln -s /opt/erlang/24.0.5/bin/ct_run .
sudo ln -s /opt/erlang/24.0.5/bin/dialyzer .
sudo ln -s /opt/erlang/24.0.5/bin/epmd .
sudo ln -s /opt/erlang/24.0.5/bin/erlc .
sudo ln -s /opt/erlang/24.0.5/bin/run_erl .
sudo ln -s /opt/erlang/24.0.5/bin/to_erl .
sudo ln -s /opt/erlang/24.0.5/bin/typer .

sudo wget https://s3.amazonaws.com/rebar3/rebar3 
sudo chmod +x rebar3

