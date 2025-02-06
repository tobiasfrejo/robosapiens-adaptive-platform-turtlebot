#pragma once

#include "std_msgs/msg/u_int16_multi_array.hpp"
#include <QTextEdit>
#include <QPushButton>
#include <QRadioButton>
#include <QGroupBox>
#include <rviz_common/panel.hpp>
#include <rviz_common/ros_integration/ros_node_abstraction_iface.hpp>
#include <std_msgs/msg/string.hpp>
#include "spin_interfaces/msg/spin_periodic_commands.hpp"
#include <array>
#include <vector>
#include <utility>
#include <string_view>
#include <algorithm>
#include <frozen/unordered_map.h>
#include <frozen/map.h>
#include <frozen/string.h>
#include <array>

namespace spin_panel
{
  constexpr std::uint16_t operator""_u(unsigned long long value)
  {
    return static_cast<std::uint16_t>(value);
  }

  enum class bot_variant
  {
    TB3_Sim,
    TB3_Real,
    TB4_Sim,
    TB4_Real,
  };

  enum class occlusion_direction
  {
    NW,
    NE,
    SW,
    SE,
    None,
    Entire,
  };

  static constexpr std::array<bot_variant, 4>
      BOTS = {bot_variant::TB3_Sim, bot_variant::TB3_Real, bot_variant::TB4_Sim, bot_variant::TB4_Real};

  static constexpr frozen::unordered_map<bot_variant, frozen::string, 4> BOT_NAMES = {
      {bot_variant::TB3_Sim, "TurtleBot3 sim"},
      {bot_variant::TB3_Real, "TurtleBot3 real"},
      {bot_variant::TB4_Sim, "TurtleBot4 sim"},
      {bot_variant::TB4_Real, "TurtleBot4 real"},
  };

  static constexpr frozen::unordered_map<bot_variant, uint16_t, 4> BOT_LIDAR_SIZES = {
      {bot_variant::TB3_Sim, 360_u},
      {bot_variant::TB3_Real, 360_u},
      {bot_variant::TB4_Sim, 640_u},
      {bot_variant::TB4_Real, 1080_u},
  };

  static constexpr frozen::unordered_map<bot_variant, uint16_t, 4> BOT_LIDAR_ROTATIONS = {
      {bot_variant::TB3_Sim, 0_u},
      {bot_variant::TB3_Real, 0_u},
      {bot_variant::TB4_Sim, 0_u},
      {bot_variant::TB4_Real, 90_u},
  };

  static constexpr std::array<occlusion_direction, 6> DIRECTIONS = {occlusion_direction::NW, occlusion_direction::NE, occlusion_direction::SW, occlusion_direction::SE, occlusion_direction::None, occlusion_direction::Entire};

  static constexpr frozen::unordered_map<occlusion_direction, frozen::string, 6> DIRECTION_NAMES = {
      {occlusion_direction::NW, "Northwest"},
      {occlusion_direction::NE, "Northeast"},
      {occlusion_direction::SW, "Southwest"},
      {occlusion_direction::SE, "Southeast"},
      {occlusion_direction::None, "No occlusion"},
      {occlusion_direction::Entire, "Entire lidar"},
  };

  namespace detail
  {
    struct BotOcc
    {
      bot_variant bot = bot_variant::TB3_Sim;
      occlusion_direction occ = occlusion_direction::NW;
    };

    constexpr bool operator==(const BotOcc &lhs, const BotOcc &rhs)
    {
      return lhs.bot == rhs.bot && lhs.occ == rhs.occ;
    }

    constexpr bool operator<(const BotOcc &lhs, const BotOcc &rhs)
    {
      return lhs.bot < rhs.bot || (lhs.bot == rhs.bot && lhs.occ < rhs.occ);
    }

    static constexpr auto DONT_CARE = std::make_pair(std::numeric_limits<uint16_t>::max(), std::numeric_limits<uint16_t>::max());

    static constexpr frozen::unordered_map<occlusion_direction,
                                           std::array<std::pair<uint16_t, uint16_t>, 2>, 6>
        DIRECTION_OCCLUSIONS = {
            {occlusion_direction::NW, {{{90_u, 360_u}, DONT_CARE}}},
            {occlusion_direction::NE, {{{0_u, 270_u}, DONT_CARE}}},
            {occlusion_direction::SW, {{{0_u, 90_u}, {180_u, 360_u}}}},
            {occlusion_direction::SE, {{{0_u, 180_u}, {270_u, 360_u}}}},
            {occlusion_direction::None, {{{0_u, 360_u}, DONT_CARE}}},
            {occlusion_direction::Entire, {{DONT_CARE, DONT_CARE}}},
    };

    constexpr std::array<std::pair<uint16_t, uint16_t>, 2> rotate_occlusions(const BotOcc &bot_occ)
    {
      constexpr auto apply_rotation = [](std::pair<uint16_t, uint16_t> pair, uint16_t rotation, uint16_t lidar_size) -> std::pair<uint16_t, uint16_t>
      {
        if (pair == DONT_CARE)
        {
          return pair;
        }
        const auto first_tmp = static_cast<float>(pair.first) / 360.0f * lidar_size;
        const auto second_tmp = static_cast<float>(pair.second) / 360.0f * lidar_size;
        const auto rot = static_cast<float>(rotation) / 360.0f * lidar_size;
        const auto first = static_cast<uint16_t>(first_tmp + rot) % lidar_size;
        const auto second = static_cast<uint16_t>(second_tmp + rot) % lidar_size;
        if (second == 0)
        {
          return std::make_pair(first, lidar_size);
        }
        else
        {
          return std::make_pair(first, second);
        }
      };
      const auto rotation = BOT_LIDAR_ROTATIONS.at(bot_occ.bot);
      const auto init_occlusions = DIRECTION_OCCLUSIONS.at(bot_occ.occ);
      const auto lidar_samples = BOT_LIDAR_SIZES.at(bot_occ.bot);
      if (init_occlusions[0] == DONT_CARE && init_occlusions[1] == DONT_CARE)
      {
        return init_occlusions;
      }
      else if (init_occlusions[1] == DONT_CARE)
      {
        // The scenario where either the first coordinate overflows after rotation and we need to wrap around
        // Or where we can just increase
        const auto [first, second] = apply_rotation(init_occlusions[0], rotation, lidar_samples);
        if (second < first)
        {
          // If (a, b) where b < a then [(0, b), (a, 360)]
          std::array<std::pair<uint16_t, uint16_t>, 2> occlusions{{{0, second},
                                                                   {first, lidar_samples}}};
          return occlusions;
        }
        else
        {
          return {std::make_pair(first, second), DONT_CARE};
        }
      }
      else
      {
        const auto lower_region = apply_rotation(init_occlusions[0], rotation, lidar_samples);
        const auto upper_region = apply_rotation(init_occlusions[1], rotation, lidar_samples);
        if (lower_region.second < lower_region.first && upper_region.second < upper_region.first)
        {
          // Ill-formed config. This would require an array of 4...
          // We can't have two occlusions that wrap around
          return {DONT_CARE, DONT_CARE};
        }
        else if (lower_region.first == upper_region.second)
        {
          // An example of this case is [(0, 90), (180, 360)] with a rotation = 90 and lidar_samples = 360.
          // Without handling edge case this becomes: [(90, 180), (270, 90)]
          // Need to transform it into [(0, 180), (270, 360)]
          return {std::make_pair(0, lower_region.second), std::make_pair(upper_region.first, lidar_samples)};
        }
        else
        {
          return {lower_region, upper_region};
        }
      }
    }

    constexpr auto occlusions_pair_array()
    {
      constexpr auto pair_with_occlusion = [](const BotOcc &bot_occ)
      {
        return std::make_pair(bot_occ, rotate_occlusions(bot_occ));
      };

      std::array<std::pair<BotOcc, std::array<std::pair<uint16_t, uint16_t>, 2>>, BOTS.size() * DIRECTIONS.size()> arr{};
      for (size_t i = 0; i < BOTS.size(); i++)
      {
        for (size_t j = 0; j < DIRECTIONS.size(); j++)
        {
          arr[i * DIRECTIONS.size() + j] = pair_with_occlusion(BotOcc{BOTS[i], DIRECTIONS[j]});
        }
      }
      return arr;
    }

    // TODO: Make this return unordered map instead - I just can't get the hashing to work
    constexpr auto make_occlusions_map()
    {
      return frozen::make_map(occlusions_pair_array());
    }
  } // namespace detail

  class SpinPanel : public rviz_common::Panel
  {
    Q_OBJECT
  public:
    explicit SpinPanel(QWidget *parent = 0);
    ~SpinPanel() override;

    void onInitialize() override;

  protected:
    std::shared_ptr<rviz_common::ros_integration::RosNodeAbstractionIface>
        node_ptr_;
    rclcpp::Publisher<std_msgs::msg::UInt16MultiArray>::SharedPtr publisher_;
    rclcpp::Subscription<spin_interfaces::msg::SpinPeriodicCommands>::SharedPtr subscription_;

    void topicCallback(const spin_interfaces::msg::SpinPeriodicCommands &msg);

    QTextEdit *label_;
    QPushButton *button_;
    QRadioButton *bot_variant_selected_;
    QGroupBox *bot_variants_;
    QRadioButton *region_variant_selected_;
    QGroupBox *region_variants_;

  private Q_SLOTS:
    void buttonActivated();
  };
} // namespace spin_panel
