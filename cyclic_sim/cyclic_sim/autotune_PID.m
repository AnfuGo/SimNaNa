function gains = tuneControllers(num_list, den_list, controller_type, method, wc)

% tuneControllers
% Sintonia automática de múltiplas funções de transferência
%
% INPUTS:
% num_list         → cell array com numeradores
% den_list         → cell array com denominadores
% controller_type  → 'P', 'PI', 'PID'
% method           → 'pidtune' ou 'looptune'
% wc               → [wmin wmax] (somente looptune)
%
% OUTPUT:
% gains → matriz [Kp Ki Kd Ti Td]

controller_type = upper(controller_type);
method = lower(method);

n_systems = length(num_list);

% Pré-aloca matriz
gains = zeros(n_systems, 5);

for i = 1:n_systems

    numG = num_list{i};
    denG = den_list{i};

    G = tf(numG, denG);

    try

        %% ===== PIDTUNE =====
        if strcmp(method, 'pidtune')

            C = pidtune(G, controller_type);

        %% ===== LOOPTUNE =====
        elseif strcmp(method, 'looptune')

            if nargin < 5 || isempty(wc)
                error('Faixa wc necessária para looptune');
            end

            Cblk = tunablePID('Cblk', lower(controller_type));

            [~, Ctuned] = looptune(G, Cblk, wc);

            C = getBlockValue(Ctuned, 'Cblk');

        else
            error('Método inválido');
        end

        %% Extrai ganhos
        Kp = C.Kp;

        if strcmp(controller_type, 'P')
            Ki = 0;
            Kd = 0;

        elseif strcmp(controller_type, 'PI')
            Ki = C.Ki;
            Kd = 0;

        elseif strcmp(controller_type, 'PID')
            Ki = C.Ki;
            Kd = C.Kd;

        else
            error('Tipo de controlador inválido');
        end

        %% Tempos equivalentes
        if Ki ~= 0
            Ti = Kp / Ki;
        else
            Ti = 0;
        end

        if Kd ~= 0
            Td = Kd / Kp;
        else
            Td = 0;
        end

        %% Armazena
        gains(i, :) = [Kp Ki Kd Ti Td];

    catch ME

        warning('Erro na planta %d: %s', i, ME.message);

        gains(i, :) = [NaN NaN NaN NaN NaN];

    end

end

end