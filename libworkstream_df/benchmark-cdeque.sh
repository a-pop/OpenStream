b=3
d=15
mu=$(awk "BEGIN{print ($b ^ $d) / 10}")
nthread=2
niter=200
while getopts b:d:f:n:pr:t: opt; do
	case $opt in
	b)
		b=$OPTARG
		;;
	d)
		d=$OPTARG
		;;
	f)
		mu=$OPTARG
		;;
	n)
		nthread=$OPTARG
		;;
	p)
		dry=1
		;;
	r)
		randfile=$OPTARG
		;;
	t)
		niter=$OPTARG
	esac
done
shift $((OPTIND - 1))

if [ $# -eq 0 ]; then
	tests='test-cdeque test-cdeque-nofences test-cdeque-c11 test-cdeque-dumbc11'
else
	for t; do
		if [ ${t%-nosync} = $t ]; then
			tests="$tests ${t#./}"
		else
			nosync=1
		fi
	done
fi
testargs="-b $b -d $d -n $nthread"

if [ "$nosync" ] || [ -z "$randfile" ]; then
	t=test-cdeque-nosync
	echo $t prerun >&2
	for i in $(seq 1 10); do
		[ $dry ] || ./$t $testargs -f 0 | tail -n 1 >/dev/null
	done
	log=$t.$nthread.$b.$d.log
	for i in $(seq 1 30); do
		echo $t $testargs -f 0 >&2 \>\> $log
		[ $dry ] || ./$t $testargs -f 0 | tail -n 1 >$log
	done
fi
if [ -z "$randfile" ]; then
	randfile=rand.$$
	awk -v ni=$niter -v mu=$mu '
	BEGIN {
		for (i = 1; i <= ni; ++i) {
			do
				x = -log(rand()) * mu
			while (mu <= 1.0 && x > 1.0)
			print x
		}
	}
	' >"$randfile"
fi

for t in $tests; do
	echo $t prerun >&2
	for i in $(seq 1 10); do
		[ $dry ] || ./$t $testargs -f 0 | tail -n 1 >/dev/null
	done
	log=$t.$nthread.$b.$d.log
	while read x; do
		f=$(awk "BEGIN{print $mu <= 1.0 ? $x : $x / ($nthread-1)}")
		echo $t $testargs -f $f >&2 \>\> $log
		[ $dry ] || ./$t $testargs -f $f | tail -n 1 >>$log
	done <"$randfile"
done
