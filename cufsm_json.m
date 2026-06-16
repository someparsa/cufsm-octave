% Public script wrapper for JSON-driven CUFSM analysis.
% Usage:
%   octave-cli --quiet cufsm_json.m examples/lipped-channel.json

args = argv();
if length(args) < 1
    error('Usage: octave-cli --quiet cufsm_json.m path/to/input.json');
end

script_location = fileparts(mfilename('fullpath'));
if isempty(script_location)
    script_location = pwd;
end
addpath(fullfile(script_location,'helpers'));

cufsm_json_run(args{1});
